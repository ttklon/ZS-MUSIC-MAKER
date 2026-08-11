"""
[v8] hw_autodetect.py — единый детектор железа с чёткими режимами.

ТЗ 20.1 [ЖЕЛЕЗО]:
  • Целевая платформа: 2× Xeon, 24 GB RAM, 12 GB VRAM, Windows 11 → mode="full"
  • Fallback: RX 580 4GB / 16 GB RAM / 1× Xeon        → mode="lite"

Режимы:
  full — MusicGen-large, RVC-full, XTTS клон, Bark-full, длинные окна.
  mid  — MusicGen-medium, RVC-medium, Silero, средние окна (6-8 GB VRAM).
  lite — MusicGen-small (CPU), RVC-lite (CPU/DirectML), Silero, короткие окна.

Возвращает dict, который используют Orchestrator, MusicGen, RVC, Voice Synth.
"""

from __future__ import annotations

import json
import os
import platform
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HW_CACHE = ROOT / "data" / "hw_profile.json"
HW_CACHE.parent.mkdir(parents=True, exist_ok=True)


def _cpu_info() -> dict:
    info = {
        "logical": os.cpu_count() or 1,
        "arch": platform.machine(),
        "system": platform.system(),
        "release": platform.release(),
    }
    try:
        import psutil

        info["ram_gb"] = round(psutil.virtual_memory().total / (1024**3), 1)
    except Exception:
        info["ram_gb"] = 0.0
    return info


def _gpu_info() -> dict:
    """Определяем видеокарту и VRAM: CUDA → DirectML → ROCm → CPU."""
    g = {"kind": "cpu", "name": "CPU only", "vram_gb": 0.0, "ok": True}
    # NVIDIA CUDA
    try:
        import torch

        if torch.cuda.is_available():
            g["kind"] = "cuda"
            g["name"] = torch.cuda.get_device_name(0)
            g["vram_gb"] = round(
                torch.cuda.get_device_properties(0).total_memory / (1024**3), 1
            )
            return g
    except Exception:
        pass
    # DirectML (AMD/Intel iGPU на Windows)
    try:
        import torch_directml as dml

        g["kind"] = "directml"
        try:
            g["name"] = dml.device_name(0)
        except Exception:
            g["name"] = "DirectML GPU"
        # DirectML не даёт точный VRAM. Пробуем через WMIC на Windows.
        try:
            import subprocess

            out = subprocess.check_output(
                [
                    "wmic",
                    "path",
                    "win32_VideoController",
                    "get",
                    "AdapterRAM,Name",
                    "/format:csv",
                ],
                timeout=5,
                stderr=subprocess.DEVNULL,
            ).decode(errors="ignore")
            for line in out.splitlines():
                parts = [p.strip() for p in line.split(",") if p.strip()]
                if len(parts) >= 3 and parts[-1].isdigit():
                    v = int(parts[-1]) / (1024**3)
                    if v > g["vram_gb"]:
                        g["vram_gb"] = round(v, 1)
                        g["name"] = parts[-2]
        except Exception:
            g["vram_gb"] = 4.0  # осторожная оценка для RX 580
        return g
    except Exception:
        pass
    # ROCm (Linux)
    try:
        if os.path.exists("/opt/rocm"):
            g["kind"] = "rocm"
            g["name"] = "AMD ROCm GPU"
            g["vram_gb"] = 8.0
            return g
    except Exception:
        pass
    return g


def detect(force: bool = False) -> dict:
    """Полное определение. Кэш в data/hw_profile.json (24 часа)."""
    if not force and HW_CACHE.exists():
        try:
            cached = json.loads(HW_CACHE.read_text(encoding="utf-8"))
            if time.time() - cached.get("ts", 0) < 86400:
                return cached
        except Exception:
            pass

    cpu = _cpu_info()
    gpu = _gpu_info()
    ram = cpu.get("ram_gb", 0.0)
    vram = gpu.get("vram_gb", 0.0)

    # Определяем режим
    if gpu["kind"] == "cuda" and vram >= 10 and ram >= 20:
        mode = "full"
        reason = "CUDA 10+ GB VRAM, 20+ GB RAM"
    elif vram >= 10 and ram >= 20:
        mode = "full"
        reason = "10+ GB VRAM (не-CUDA) + 20+ GB RAM"
    elif vram >= 6 and ram >= 16:
        mode = "mid"
        reason = "6-10 GB VRAM"
    elif vram >= 3 and ram >= 12:
        mode = "lite"
        reason = "3-6 GB VRAM (RX 580 fallback)"
    else:
        mode = "lite"
        reason = "CPU only / малый VRAM"

    profile = {
        "cpu": cpu,
        "gpu": gpu,
        "mode": mode,
        "reason": reason,
        "ts": time.time(),
        "recommendations": _recommendations(mode, vram, ram, gpu["kind"]),
    }
    try:
        HW_CACHE.write_text(
            json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass
    return profile


def _recommendations(mode: str, vram: float, ram: float, gpu_kind: str) -> dict:
    if mode == "full":
        return {
            "musicgen": "large (12 GB VRAM)",
            "rvc": "full retraining + inference",
            "voice_synth": "Bark-full + XTTS + Silero",
            "windows_len_sec": 30,
            "queue_parallelism": 2,
            "quality_mode": "quality",
        }
    if mode == "mid":
        return {
            "musicgen": "medium (6-8 GB VRAM)",
            "rvc": "inference + light training",
            "voice_synth": "Silero + Bark-small",
            "windows_len_sec": 15,
            "queue_parallelism": 1,
            "quality_mode": "quality",
        }
    return {
        "musicgen": "small (CPU) + опционально MusicGen-melody-only",
        "rvc": (
            "inference обязательно, training в ночном режиме " "≤3 часа"
            if gpu_kind != "cpu"
            else "только inference, training только ночью на CPU"
        ),
        "voice_synth": "Silero v4 (CPU)",
        "windows_len_sec": 8,
        "queue_parallelism": 1,
        "quality_mode": "quality",  # даже на lite — качество приоритет
    }


def human_summary(profile: dict) -> str:
    """Красивый текст для GUI."""
    cpu = profile["cpu"]
    gpu = profile["gpu"]
    lines = [
        f"🖥  Режим: {profile['mode'].upper()}  ({profile['reason']})",
        f"CPU: {cpu.get('logical', '?')} потоков · RAM: {cpu.get('ram_gb', 0)} GB",
        f"GPU: {gpu.get('name', '?')} ({gpu.get('kind')}, {gpu.get('vram_gb', 0)} GB VRAM)",
        "",
        "Рекомендуемая конфигурация:",
    ]
    for k, v in profile.get("recommendations", {}).items():
        lines.append(f"  • {k}: {v}")
    return "\n".join(lines)


if __name__ == "__main__":
    p = detect(force=True)
    print(json.dumps(p, ensure_ascii=False, indent=2))
    print()
    print(human_summary(p))

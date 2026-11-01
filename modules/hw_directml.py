"""
ZS Music Maker v10 — DirectML / AMD ускорение
==============================================
ТЗ 15.2: если решение требует NVIDIA CUDA, а у пользователя AMD —
ищем альтернативу (DirectML, CPU-режим, ONNX).

Автодетект и настройка torch-directml для AMD RX 580 на Windows.
Также логика fallback на CPU и оценка VRAM.
"""

from __future__ import annotations

import json
import logging
import platform
import subprocess
from pathlib import Path
from typing import Any

log = logging.getLogger("zsmm.hw_directml")


def detect() -> dict[str, Any]:
    """
    Возвращает {gpu_kind, backend, device_str, vram_mb, recommendations}
    """
    out = {
        "os": platform.system(),
        "arch": platform.machine(),
        "gpu_kind": "unknown",
        "backend": "cpu",
        "device_str": "cpu",
        "vram_mb": 0,
        "torch_cuda": False,
        "torch_directml": False,
        "recommendations": [],
    }

    # 1) torch + CUDA
    try:
        import torch

        if torch.cuda.is_available():
            out["torch_cuda"] = True
            out["gpu_kind"] = "nvidia"
            out["backend"] = "cuda"
            out["device_str"] = "cuda:0"
            try:
                props = torch.cuda.get_device_properties(0)
                out["vram_mb"] = int(props.total_memory / (1024 * 1024))
                out["gpu_name"] = props.name
            except Exception:
                logging.getLogger(__name__).debug("ignored exception", exc_info=True)
    except Exception as e:
        log.debug("no torch cuda: %s", e)

    # 2) DirectML (AMD/Intel на Windows)
    if out["backend"] == "cpu":
        try:
            import torch_directml  # type: ignore

            out["torch_directml"] = True
            n = torch_directml.device_count()
            if n > 0:
                out["backend"] = "directml"
                out["device_str"] = "privateuseone:0"
                out["gpu_kind"] = "amd_or_intel"
                out["gpu_name"] = torch_directml.device_name(0)
        except Exception as e:
            log.debug("no directml: %s", e)

    # 3) Оценка VRAM через wmic (Windows only) для AMD
    if (
        out["gpu_kind"] in ("amd_or_intel", "unknown")
        and platform.system() == "Windows"
    ):
        vram = _wmic_vram_mb()
        if vram > 0:
            out["vram_mb"] = vram

    # Рекомендации
    if out["backend"] == "cpu":
        out["recommendations"].append(
            "GPU-ускорение недоступно. MusicGen/RVC будут работать медленно на CPU. "
            "Используйте лёгкие модели (musicgen-small, RVC 40k)."
        )
    elif out["vram_mb"] and out["vram_mb"] < 6000:
        out["recommendations"].append(
            f"VRAM {out['vram_mb']} MB — включён режим экономии: batch=1, precision=fp16, "
            f"musicgen-small, RVC поэтапно."
        )
    elif out["vram_mb"] and out["vram_mb"] >= 12000:
        out["recommendations"].append(
            f"VRAM {out['vram_mb']} MB — доступны тяжёлые режимы: musicgen-medium/large, "
            f"RVC v2 полный трейн, batch=4."
        )

    return out


def _wmic_vram_mb() -> int:
    try:
        r = subprocess.run(
            ["wmic", "path", "win32_VideoController", "get", "AdapterRAM"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        max_bytes = 0
        for line in r.stdout.splitlines():
            line = line.strip()
            if line.isdigit():
                max_bytes = max(max_bytes, int(line))
        return max_bytes // (1024 * 1024)
    except Exception:
        return 0


def save_profile(out_json: str = "data/hw_profile_v10.json") -> dict[str, Any]:
    prof = detect()
    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(prof, f, ensure_ascii=False, indent=2)
    return prof


def choose_musicgen_variant(profile: dict[str, Any] | None = None) -> str:
    """
    Возвращает 'small' / 'medium' / 'large' в зависимости от железа.
    """
    if profile is None:
        profile = detect()
    vram = profile.get("vram_mb", 0)
    if profile.get("backend") == "cpu":
        return "small"
    if vram >= 12000:
        return "large"
    if vram >= 8000:
        return "medium"
    return "small"


if __name__ == "__main__":
    p = save_profile()
    print(json.dumps(p, ensure_ascii=False, indent=2))

# -*- coding: utf-8 -*-
"""
modules.hit_factory.adaptive — адаптация под любое железо.

Определяет, что можно запустить на текущем компе (RAM/VRAM/GPU) и
подбирает лёгкий/тяжёлый путь без падения. Работает на любом PC:
от 3.85GB RAM + 2 CPU (текущий стенд) до топ GPU.

Логика:
- RAM <4GB или нет GPU → чистый DSP (как сейчас), короткие треки 30-60с, 1-2 попытки
- RAM 4-8GB → можно Silero CPU (59МБ) + ACE-Step turbo 2B если сервер есть
- RAM >8GB + VRAM >6GB → MusicGen-medium, XTTS, Demucs, SDXL и т.д.
- AMD Radeon → пробуем ROCm → DirectML → CPU fallback (никогда не падаем)
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

_LOG = logging.getLogger(__name__)

def _get_ram() -> float:
    try:
        import psutil
        return round(psutil.virtual_memory().total / (1024**3), 2)
    except Exception:
        return 0.0

def _get_free_ram() -> float | None:
    try:
        import psutil
        return round(psutil.virtual_memory().available / (1024**3), 2)
    except Exception:
        return None

def _detect_gpu() -> dict:
    """Возвращает {backend, vendor, vram_total, vram_free, name} или {}."""
    # пытаемся через app/ai/hardware если есть
    try:
        from app.ai.hardware import detect_system
        sysinfo = detect_system()
        torch_dev = sysinfo.get("pytorch_device") or {}
        gpus = sysinfo.get("gpus") or []
        # берём первый не-unknown
        vendor = "unknown"
        if torch_dev:
            vendor = torch_dev.get("vendor") or "unknown"
            return {
                "backend": torch_dev.get("backend", "cpu"),
                "vendor": vendor,
                "vram_total": torch_dev.get("total_vram_gib"),
                "vram_free": torch_dev.get("free_vram_gib"),
                "name": torch_dev.get("name", ""),
                "gpus": gpus,
            }
        if gpus:
            # эвристика по имени
            name = gpus[0].get("name", "")
            vendor = gpus[0].get("vendor", "unknown")
            return {"backend": "directml" if vendor == "amd" else "cpu", "vendor": vendor, "name": name, "gpus": gpus}
    except Exception as e:
        _LOG.debug(f"hardware detect failed: {e}")
    # fallback — пробуем torch напрямую
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            free = None
            try:
                free = torch.cuda.mem_get_info(0)[0] / (1024**3)
            except Exception:
                pass
            vendor = "amd" if "amd" in name.lower() or "radeon" in name.lower() else "nvidia" if "nvidia" in name.lower() else "unknown"
            backend = "rocm" if getattr(getattr(torch, "version", None), "hip", None) else "cuda"
            return {"backend": backend, "vendor": vendor, "vram_total": round(total,2), "vram_free": round(free,2) if free else None, "name": name}
    except Exception:
        pass
    # DirectML
    try:
        import torch_directml  # type: ignore
        cnt = torch_directml.device_count()
        if cnt > 0:
            name = torch_directml.device_name(0)
            vendor = "amd" if "amd" in name.lower() or "radeon" in name.lower() else "unknown"
            return {"backend": "directml", "vendor": vendor, "name": name}
    except Exception:
        pass
    return {"backend": "cpu", "vendor": "unknown", "name": "CPU"}

def get_adaptive_config(overrides: dict | None = None) -> dict:
    """
    Возвращает адаптивный конфиг для HitFactory под текущее железо.
    Можно передать overrides для форса (например, для тестов).
    """
    ram = _get_ram()
    free_ram = _get_free_ram()
    gpu = _detect_gpu()
    backend = gpu.get("backend", "cpu")
    vendor = gpu.get("vendor", "unknown")
    vram_total = gpu.get("vram_total") or 0
    vram_free = gpu.get("vram_free")

    # проверяем, есть ли ACE-Step сервер рядом
    aceserver = False
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        # стандартный порт ACE-Step 8001, пробуем локально
        aceserver = s.connect_ex(("127.0.0.1", 8001)) == 0
        s.close()
    except Exception:
        aceserver = False

    # проверяем torch/Silero наличие
    has_torch = False
    try:
        import torch  # noqa: F401
        has_torch = True
    except Exception:
        has_torch = False

    # эвристика уровней
    # level 0 — ультра-лайт (текущий стенд 3.85GB, 2 CPU, без GPU)
    # level 1 — лайт+ (4-8GB RAM, есть torch CPU)
    # level 2 — средний (8-16GB RAM + 4-6GB VRAM)
    # level 3 — тяж (16GB+ RAM + 8GB+ VRAM + CUDA/ROCm)
    if ram < 4.0 or (free_ram is not None and free_ram < 2.0):
        level = 0
    elif ram < 8.0 or (vram_total and vram_total < 4):
        level = 1
    elif ram < 16.0 or (vram_total and vram_total < 8):
        level = 2
    else:
        level = 3

    # AMD Radeon особая ветка: на Windows без ROCm — только DirectML/CPU, поэтому уровень не выше 1 без проверки
    if vendor == "amd" and backend in ("cpu", "directml"):
        # даже с 8GB RAM, если нет ROCm, не форсим тяжёлые CUDA-модели
        level = min(level, 1 if not has_torch else 2)

    # формируем конфиг — даже на слабом железе делаем 90с чтобы не звучал как заставка
    cfg = {
        "ram_gb": ram,
        "free_ram_gb": free_ram,
        "gpu": gpu,
        "level": level,
        "level_name": ["ultra_light (DSP only, enhanced)", "light (Silero CPU)", "medium (ACE-Step turbo)", "heavy (full AI)"][level],
        "duration_sec": [90, 90, 90, 120][level],
        "max_attempts": [3, 3, 3, 3][level],
        "human_preset": ["standard", "standard", "standard", "max"][level],
        "use_acestep": aceserver and level >= 1,  # если сервер есть — можно уже на light
        "use_musicgen": level >= 2 and has_torch and vram_total >= 6,
        "use_silero": has_torch and free_ram is not None and free_ram >= 3.0,  # Silero ~59MB + torch
        "use_bark_xtts": level >= 2 and has_torch and vram_total >= 6,
        "use_rvc": level >= 1,  # RVC в отдельном venv, лёгкий
        "use_demucs": level >= 3,
        "allow_long": True,
        "enhanced_dsp": True,  # всегда усиливаем DSP даже без нейросетей
        "note": f"AMD={vendor=='amd'} backend={backend} vram={vram_total} aceserver={aceserver} has_torch={has_torch}",
    }
    if overrides:
        cfg.update(overrides)
    return cfg

def log_adaptive() -> dict:
    cfg = get_adaptive_config()
    _LOG.info(f"[adaptive] level={cfg['level']} ({cfg['level_name']}) ram={cfg['ram_gb']} gpu={cfg['gpu'].get('name')} backend={cfg['gpu'].get('backend')} aceserver={cfg['use_acestep']}")
    print(f"[ADAPTIVE] {cfg['level_name']} | RAM {cfg['ram_gb']}GB free {cfg['free_ram_gb']} | GPU {cfg['gpu'].get('name')} ({cfg['gpu'].get('backend')}/{cfg['gpu'].get('vendor')}) VRAM {cfg['gpu'].get('vram_total')} | ACE-Step server: {cfg['use_acestep']} | Silero: {cfg['use_silero']}")
    return cfg

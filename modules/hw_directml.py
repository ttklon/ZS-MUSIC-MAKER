"""Compatibility API for hardware diagnostics; detection lives in app.ai.hardware."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def detect() -> dict[str, Any]:
    from app.ai.hardware import detect_system

    system = detect_system()
    device = system["pytorch_device"] or {}
    dml = system["directml_devices"]
    gpu = device or (dml[0] if dml else (system["gpus"][0] if system["gpus"] else {}))
    backend = device.get("backend") or ("directml" if dml else "cpu")
    return {
        "os": system["os"], "arch": system["architecture"],
        "gpu_kind": gpu.get("vendor", "unknown"), "gpu_name": gpu.get("name", "unknown"),
        "backend": backend, "device_str": "cuda:0" if device else "cpu",
        "vram_mb": int((device.get("total_vram_gib") or 0) * 1024),
        "torch_cuda": backend == "cuda", "torch_directml": bool(dml),
        "ram_available_gib": system["ram_available_gib"], "disk_free_gib": system["disk_free_gib"],
        "recommendations": ["Наличие DirectML не подтверждает совместимость конкретной модели; "
                            "общие загрузчики используют PyTorch или CPU."],
    }


def save_profile(out_json: str = "data/hw_profile.json") -> dict[str, Any]:
    profile = detect()
    path = Path(out_json)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    return profile


def choose_musicgen_variant(profile: dict[str, Any] | None = None) -> str:
    """Conservative hint only; MusicGen is not validated by hardware detection."""
    profile = profile or detect()
    if profile.get("backend") not in ("cuda", "rocm"):
        return "small"
    vram = profile.get("vram_mb", 0)
    if vram >= 12000:
        return "large"
    if vram >= 8000:
        return "medium"
    return "small"

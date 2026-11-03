"""Compatibility profile built from the shared, uncached hardware measurements."""
from __future__ import annotations

import json
import time

from app.ai.hardware import detect_system


def detect(force: bool = False) -> dict:
    """Return current RAM/VRAM/disk information; `force` kept for old callers."""
    system = detect_system()
    device = system["pytorch_device"] or {}
    available_ram = system["ram_available_gib"] or 0
    free_vram = device.get("free_vram_gib") or 0
    if device and free_vram >= 10 and available_ram >= 12:
        mode = "full"
    elif device and free_vram >= 6 and available_ram >= 8:
        mode = "mid"
    else:
        mode = "lite"
    adapters = system["gpus"]
    gpu = {
        "kind": system["default_backend"],
        "name": device.get("name") or (adapters[0]["name"] if adapters else "unknown"),
        "vendor": device.get("vendor") or (adapters[0]["vendor"] if adapters else "unknown"),
        "vram_gb": device.get("total_vram_gib") or (adapters[0].get("total_vram_gib") if adapters else None) or 0.0,
        "vram_free_gb": device.get("free_vram_gib"),
        "ok": bool(device),
    }
    return {
        "cpu": {"logical": system["cpu_threads"], "physical": system["cpu_cores"],
                "ram_gb": system["ram_total_gib"], "ram_available_gb": system["ram_available_gib"],
                "arch": system["architecture"], "system": system["os"], "release": system["os_version"]},
        "gpu": gpu, "system": system, "mode": mode,
        "reason": "Приблизительная категория по свободной памяти PyTorch; не проверка моделей",
        "ts": time.time(),
        "recommendations": {
            "models": "Выбирать под свободную память; наличие железа не подтверждает совместимость модели",
            "rvc": "Встроенное обучение не подключено; для преобразования нужна своя модель и рабочий backend",
            "directml": "Обнаружение DirectML не означает, что конкретный движок его поддерживает",
            "queue_parallelism": 1,
        },
    }


def get_hardware_profile() -> dict:
    return detect()


def human_summary(profile: dict) -> str:
    system = profile["system"]
    device = profile["gpu"]
    return (f"CPU: {system['cpu_name']} · threads: {system['cpu_threads']}\n"
            f"RAM GiB total/available: {system['ram_total_gib']} / {system['ram_available_gib']}\n"
            f"Disk free GiB: {system['disk_free_gib']}\n"
            f"GPU: {device['name']} · PyTorch backend: {device['kind']} · "
            f"VRAM GiB total/free: {device['vram_gb'] or 'unknown'} / {device['vram_free_gb']}\n"
            f"All detected GPUs: {', '.join(gpu['name'] for gpu in system['gpus']) or 'unknown'}\n"
            f"DirectML devices: {len(system['directml_devices'])} (not necessarily supported by model)\n"
            f"{system['notice']}")


if __name__ == "__main__":
    p = detect(force=True)
    print(json.dumps(p, ensure_ascii=False, indent=2))
    print(human_summary(p))

"""Measured capability inventory; no invented minimum or accepted GPU profile."""
from __future__ import annotations

import math
import os
import platform
import shutil


def measure_profile(directory) -> dict:
    measurements = {"cpu_threads": os.cpu_count(), "ram_total_gib": None, "ram_available_gib": None,
                    "disk_free_gib": None, "gpu": "not_measured"}
    errors = []
    try:
        import psutil
        memory = psutil.virtual_memory()
        measurements.update(ram_total_gib=round(memory.total / 2**30, 2),
                            ram_available_gib=round(memory.available / 2**30, 2))
    except Exception as exc:
        errors.append(f"RAM: {type(exc).__name__}: {exc}")
    try:
        measurements["disk_free_gib"] = round(shutil.disk_usage(directory).free / 2**30, 2)
    except Exception as exc:
        errors.append(f"disk: {type(exc).__name__}: {exc}")
    return {"schema": 1, "os": platform.system(), "os_release": platform.release(),
            "architecture": platform.machine(), "measurements": measurements, "errors": errors,
            "kind": "inventory_only", "inference_verified": False, "product_profile_accepted": False,
            "profiles": [{"id": name, "status": "unverified", "evidence": []}
                         for name in ("windows_cpu", "windows_cuda", "windows_amd")],
            "warning": "Ресурсы измерены для диагностики, не для обещания скорости, пения или поддержки GPU."}


def preflight_resources(profile: dict, *, ram_gib=None, disk_gib=None) -> dict:
    """Only explicit per-engine estimates may be checked. Unknown never means enough."""
    reasons = []
    measured = profile.get("measurements", {})
    for key, needed in (("ram_available_gib", ram_gib), ("disk_free_gib", disk_gib)):
        if needed is None:
            reasons.append(f"{key}: нет утверждённого бюджета backend")
            continue
        available = measured.get(key)
        if not isinstance(needed, (int, float)) or isinstance(needed, bool) or not math.isfinite(needed) or needed <= 0:
            reasons.append(f"{key}: неверный бюджет")
        elif not isinstance(available, (int, float)) or isinstance(available, bool) or not math.isfinite(available) or available < needed:
            reasons.append(f"{key}: ресурс неизвестен или недостаточен")
    return {"allowed": not reasons, "reasons": reasons, "inference_verified": False}

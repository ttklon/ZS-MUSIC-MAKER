"""Measured capability inventory; no invented minimum or accepted GPU profile."""
from __future__ import annotations

import math
import os
import platform


def measure_profile(directory) -> dict:
    from app.ai.hardware import detect_system
    measurements = {"cpu_threads": os.cpu_count(), "ram_total_gib": None, "ram_available_gib": None,
                    "ram_available_bytes": None, "disk_free_gib": None, "disk_free_bytes": None,
                    "gpu": "not_measured"}
    errors = []
    system = {}
    try:
        system = detect_system(directory)
        for key in ("cpu_threads", "ram_total_gib", "ram_available_gib", "ram_available_bytes",
                    "disk_free_gib", "disk_free_bytes"):
            measurements[key] = system.get(key)
        device = system.get("pytorch_device") or {}
        measurements["gpu"] = {"adapters": system.get("gpus", []),
                               "pytorch_device": device or None,
                               "free_vram_gib": device.get("free_vram_gib"),
                               "free_vram_bytes": device.get("free_vram_bytes"),
                               "backend": device.get("backend", "cpu"),
                               "directml_devices": system.get("directml_devices", []),
                               "inference_verified": False}
        for key in ("ram_available_gib", "disk_free_gib"):
            if measurements[key] is None:
                errors.append(f"{key}: unavailable")
    except Exception as exc:
        errors.append(f"inventory: {type(exc).__name__}: {exc}")
    return {"schema": 1, "os": platform.system(), "os_release": platform.release(),
            "architecture": platform.machine(), "measurements": measurements, "errors": errors,
            "system": system,
            "kind": "inventory_only", "inference_verified": False, "product_profile_accepted": False,
            "profiles": [{"id": name, "status": "unverified", "evidence": []}
                         for name in ("windows_cpu", "windows_cuda", "windows_amd")],
            "warning": "Ресурсы измерены для диагностики, не для обещания скорости, пения или поддержки GPU."}


def _finite_number(value) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, TypeError, ValueError):
        return False


def _required_bytes(value) -> int | None:
    if not _finite_number(value) or value <= 0:
        return None
    try:
        return math.ceil(value * (1024 ** 3))
    except (OverflowError, ValueError):
        return None


def _available_bytes(measurements: dict, byte_key: str, gib_key: str) -> int | None:
    """Prefer exact measurements; rounded GiB is a compatibility-only fallback."""
    if byte_key in measurements:
        value = measurements.get(byte_key)
        if type(value) is int and value >= 0:
            return value
        if value is not None:
            return None  # malformed exact data must not be rescued by a display field
        # Compatibility for older inventory providers that expose only GiB.
    value = measurements.get(gib_key)
    if not _finite_number(value) or value < 0:
        return None
    try:
        # GiB display measurements are rounded to two decimals. Subtract one
        # half-unit before conversion so a rounded-up value cannot admit work.
        return math.floor(max(0.0, float(value) - 0.005) * (1024 ** 3))
    except (OverflowError, ValueError):
        return None


def preflight_resources(profile: dict, *, ram_gib=None, disk_gib=None, vram_gib=None) -> dict:
    """Compare explicit per-engine estimates with exact measurements when present.

    A rounded inventory field is accepted for older callers, but is rounded
    down before admission. Unknown, malformed, NaN and infinite values fail closed.
    """
    measured = profile.get("measurements", {}) if isinstance(profile, dict) else {}
    if not isinstance(measured, dict):
        measured = {}
    gpu = measured.get("gpu") if isinstance(measured.get("gpu"), dict) else {}
    specs = (
        ("ram_available_gib", ram_gib, _available_bytes(measured, "ram_available_bytes", "ram_available_gib")),
        ("disk_free_gib", disk_gib, _available_bytes(measured, "disk_free_bytes", "disk_free_gib")),
        ("gpu.free_vram_gib", vram_gib, _available_bytes(gpu, "free_vram_bytes", "free_vram_gib")),
    )
    reasons = []
    checks = {}
    for name, needed, available in specs:
        required = _required_bytes(needed)
        if needed is None:
            reasons.append(f"{name}: нет утверждённого бюджета backend")
            checks[name] = {"allowed": False, "required_bytes": None, "available_bytes": available}
            continue
        if required is None:
            reasons.append(f"{name}: неверный бюджет")
            checks[name] = {"allowed": False, "required_bytes": None, "available_bytes": available}
            continue
        allowed = available is not None and available >= required
        checks[name] = {"allowed": allowed, "required_bytes": required, "available_bytes": available}
        if not allowed:
            reasons.append(f"{name}: ресурс неизвестен или недостаточен")
    # VRAM is optional unless the caller supplied a budget for a selected GPU route.
    if vram_gib is None:
        checks.pop("gpu.free_vram_gib", None)
        reasons = [reason for reason in reasons if not reason.startswith("gpu.free_vram_gib:")]
    return {"allowed": not reasons, "reasons": reasons, "checks": checks, "inference_verified": False}

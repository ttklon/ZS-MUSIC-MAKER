"""Shared, fail-closed admission checks for explicitly selected beat engines.

This checks measured resource budgets against documented estimates. It does
not test model compatibility or inference and never certifies a product profile.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from app.ai.profiles import measure_profile, preflight_resources
from app.core.download_budget import RESERVE_BYTES

_GIB = 1024 ** 3
_MUSICGEN_SAMPLE_RATE = 32_000
_MUSICGEN_CHANNELS = 2
_MUSICGEN_BYTES_PER_SAMPLE = 2  # render_musicgen_beat writes PCM_16
_MUSICGEN_MODELS = {
    "small": "facebook/musicgen-small",
    "medium": "facebook/musicgen-medium",
    "large": "facebook/musicgen-large",
    "facebook/musicgen-small": "facebook/musicgen-small",
    "facebook/musicgen-medium": "facebook/musicgen-medium",
    "facebook/musicgen-large": "facebook/musicgen-large",
}


def canonical_musicgen_model(value: Any) -> Any:
    """Normalize reviewed aliases so preflight and renderer target one model ID."""
    if value is None:
        return "facebook/musicgen-small"
    return _MUSICGEN_MODELS.get(value, value) if isinstance(value, str) else value


def _measurement_summary(profile: Any) -> dict[str, Any]:
    profile = profile if isinstance(profile, dict) else {}
    measured = profile.get("measurements")
    measured = measured if isinstance(measured, dict) else {}
    gpu = measured.get("gpu")
    gpu = gpu if isinstance(gpu, dict) else {}

    def number(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        try:
            return value if math.isfinite(float(value)) and value >= 0 else None
        except (OverflowError, TypeError, ValueError):
            return None

    def byte_count(value):
        return value if type(value) is int and value >= 0 else None

    return {
        "inventory_kind": profile.get("kind") if isinstance(profile.get("kind"), str) else "unavailable",
        "ram_available_gib": number(measured.get("ram_available_gib")),
        "ram_available_bytes": byte_count(measured.get("ram_available_bytes")),
        "disk_free_gib": number(measured.get("disk_free_gib")),
        "disk_free_bytes": byte_count(measured.get("disk_free_bytes")),
        "gpu_backend": gpu.get("backend") if isinstance(gpu.get("backend"), str) else "unknown",
        "vram_available_gib": number(gpu.get("free_vram_gib")),
        "vram_available_bytes": byte_count(gpu.get("free_vram_bytes")),
    }


def _result(profile: Any, *, engine: str, status: str, reasons=(), request=None) -> dict[str, Any]:
    return {
        "schema": 1,
        "status": status,
        "scope": "selected_beat_engine",
        "engine": engine,
        "request": request,
        "measurements": _measurement_summary(profile),
        "reasons": [str(reason) for reason in reasons],
        "checks": {},
        "inference_verified": False,
        "product_profile_accepted": False,
    }


def _valid_duration(recipe: dict[str, Any]) -> int | None:
    value = recipe.get("duration_sec")
    if value is None:
        return 90
    if type(value) is not int or not 1 <= value <= 3600:
        return None
    return value


def _positive_estimate(value: Any) -> float:
    """Reject guessed/coerced budgets; the catalogue must contain a real number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("estimate must be a finite positive number")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError("estimate must be a finite positive number")
    return result


def preflight_recipe(recipe: dict[str, Any], directory: str | Path, *,
                     only: set[str] | None = None, dry_run: bool = False) -> dict[str, Any]:
    """Measure this machine and admit only the selected local MusicGen route.

    The registry's MusicGen RAM/VRAM figures are explicitly estimates. A
    1-GiB runtime reserve is added; serialized stages are sized by their peak,
    not by incorrectly summing mutually exclusive model loads. The generated
    WAV size is exact for the requested duration/format, plus the shared disk
    reserve. Checkpoint/cache download size is not known here and is not claimed.
    """
    try:
        inventory = measure_profile(Path(directory))
    except Exception as exc:  # measurement failure must become evidence, not an escape hatch
        inventory = {
            "kind": "inventory_unavailable",
            "measurements": {},
            "errors": [f"{type(exc).__name__}: {exc}"],
            "inference_verified": False,
            "product_profile_accepted": False,
        }

    recipe = recipe if isinstance(recipe, dict) else {}
    engine = recipe.get("beat_engine", "procedural")
    if not isinstance(engine, str):
        engine = "invalid"
    base = _result(inventory, engine=engine, status="not_required")
    base["inventory_errors"] = [str(item) for item in (inventory.get("errors") or [])[:8]]

    if dry_run:
        base["reasons"] = ["dry run: no model inference admitted"]
        return base
    if only is not None and "beat" not in only:
        base["reasons"] = ["beat stage skipped by caller"]
        return base
    if engine in ("procedural", "user_audio"):
        base["reasons"] = ["selected beat route does not load a neural beat model"]
        return base
    if engine == "ace_step":
        base["status"] = "blocked"
        base["request"] = {"stage": "beat", "engine": "ace_step", "required": True,
                           "resource_profile": "external_unmeasured"}
        base["reasons"] = [
            "ACE-Step service has no measured, reviewed resource budget; refusing generation (fail closed)"
        ]
        base["scope_note"] = "Local inventory cannot establish RAM/VRAM availability on the external service."
        return base
    if engine != "musicgen":
        base["status"] = "blocked"
        base["reasons"] = [f"unknown selected beat engine: {engine}"]
        return base

    base["request"] = {"stage": "beat", "engine": "musicgen", "required": True}
    raw_model = recipe.get("musicgen_model")
    if raw_model is None:
        raw_model = "facebook/musicgen-small"
    if not isinstance(raw_model, str) or raw_model not in _MUSICGEN_MODELS:
        base["status"] = "blocked"
        base["reasons"] = ["MusicGen model has no reviewed resource estimate"]
        return base
    model = canonical_musicgen_model(raw_model)
    device = recipe.get("musicgen_device")
    if device is None:
        device = "cpu"
    if device not in ("cpu", "cuda"):
        base["status"] = "blocked"
        base["reasons"] = ["MusicGen device must be cpu or cuda"]
        return base
    duration = _valid_duration(recipe)
    if duration is None:
        base["status"] = "blocked"
        base["reasons"] = ["MusicGen duration must be an integer from 1 to 3600 seconds"]
        return base

    try:
        from app.ai.model_catalog import MODEL_REGISTRY

        spec = MODEL_REGISTRY["music_generation"]
        ram_estimate = _positive_estimate(spec.get("ram_est_gb"))
        ram_required = ram_estimate + 1.0
        vram_estimate = _positive_estimate(spec.get("vram_est_gb")) if device == "cuda" else None
        vram_required = vram_estimate + 1.0 if device == "cuda" else None
    except Exception as exc:
        base["status"] = "blocked"
        base["reasons"] = [f"MusicGen resource estimate unavailable: {type(exc).__name__}"]
        return base

    # Exact PCM_16 output bound. The extra shared reserve is not an estimate of
    # the model checkpoint/cache, whose download size is currently unreviewed.
    output_bytes = duration * _MUSICGEN_SAMPLE_RATE * _MUSICGEN_CHANNELS * _MUSICGEN_BYTES_PER_SAMPLE + 44
    disk_required_bytes = RESERVE_BYTES + output_bytes
    disk_required_gib = disk_required_bytes / _GIB
    observed_backend = base["measurements"].get("gpu_backend", "unknown")
    request = {
        "stage": "beat",
        "engine": "musicgen",
        "model": model,
        "device": device,
        "observed_backend": observed_backend,
        "duration_sec": duration,
        "estimate_source": "app.ai.model_catalog.MODEL_REGISTRY.music_generation",
        "estimate_note": "The catalogue budget is for MusicGen-large; it is reused conservatively because per-size budgets are unreviewed.",
        "ram_estimate_gib": ram_estimate,
        "ram_reserve_gib": 1.0,
        "required_ram_gib": ram_required,
        "vram_estimate_gib": vram_estimate if device == "cuda" else None,
        "vram_reserve_gib": 1.0 if device == "cuda" else None,
        "required_vram_gib": vram_required,
        "required_disk_bytes": disk_required_bytes,
        "checkpoint_cache_size_known": False,
        "inference_verified": False,
    }
    resources = preflight_resources(
        inventory,
        ram_gib=ram_required,
        disk_gib=disk_required_gib,
        vram_gib=vram_required,
    )
    checks = resources["checks"]
    reasons = list(resources["reasons"])
    if device == "cuda":
        supported_backends = ("cuda", "rocm")  # PyTorch ROCm intentionally uses the cuda device API.
        backend_allowed = observed_backend in supported_backends
        checks["gpu.backend"] = {
            "allowed": backend_allowed,
            "requested_device": "cuda",
            "observed_backend": observed_backend,
            "accepted_backends": list(supported_backends),
        }
        if not backend_allowed:
            reasons.append(
                f"gpu.backend: requested CUDA device is incompatible with measured backend {observed_backend}"
            )
    base.update(
        status="allowed" if not reasons else "blocked",
        request=request,
        checks=checks,
        reasons=reasons,
        scope_note=("RAM/VRAM estimates and exact PCM WAV output disk bound are checked. "
                    "MusicGen checkpoint/cache size is unknown and is not covered by this admission result."),
    )
    return base

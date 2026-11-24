"""Hardware preflight for the canonical installed agent recipe.

This is a measured inventory and a fail-closed check for selected heavy
backends. It is not a performance certificate: the procedural path can be
attempted only when the live inventory is readable, and all model/profile
acceptance flags remain false.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any


# Operational stop floors for the opt-in procedural agent attempt. They are
# safety gates, not measured model budgets or an accepted product profile.
_AGENT_MINIMUM_RAM_AVAILABLE_GIB = 2.0
_AGENT_MINIMUM_DISK_FREE_GIB = 1.0


def _measurement_directory(output_root: str | Path) -> Path:
    """Measure the target volume without creating output directories first."""
    candidate = Path(output_root).expanduser().resolve()
    while not candidate.exists() and candidate.parent != candidate:
        candidate = candidate.parent
    return candidate


def _positive_finite(value: Any) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        numeric = float(value)
    except (OverflowError, TypeError, ValueError):
        return False
    return math.isfinite(numeric) and numeric > 0


def _capture_inventory(output_root: str | Path) -> dict:
    from app.ai.profiles import measure_profile

    try:
        inventory = measure_profile(_measurement_directory(output_root))
        if not isinstance(inventory, dict):
            raise TypeError("inventory did not return an object")
        return inventory
    except Exception as exc:  # noqa: BLE001 - malformed inventory must refuse
        return {"schema": 1, "kind": "inventory_only", "measurements": {}, "system": {},
                "errors": [f"inventory: {type(exc).__name__}: {exc}"],
                "inference_verified": False, "product_profile_accepted": False}


def _inventory_fields(inventory: dict) -> tuple[dict, dict, list[str], list[str]]:
    reasons: list[str] = []
    if (type(inventory.get("schema")) is not int or inventory.get("schema") != 1
            or inventory.get("kind") != "inventory_only"
            or inventory.get("inference_verified") is not False
            or inventory.get("product_profile_accepted") is not False):
        reasons.append("hardware inventory is not a recognized unverified measurement record")
    system_value = inventory.get("system")
    system = system_value if isinstance(system_value, dict) else {}
    if not isinstance(system_value, dict):
        reasons.append("system hardware snapshot is unavailable or malformed")
    measurements_value = inventory.get("measurements")
    measurements = measurements_value if isinstance(measurements_value, dict) else {}
    if not isinstance(measurements_value, dict):
        reasons.append("hardware measurements are unavailable or malformed")
    required = {name: measurements.get(name) for name in
                ("cpu_threads", "ram_total_gib", "ram_available_gib", "disk_free_gib")}
    for name, value in required.items():
        if not _positive_finite(value):
            reasons.append(f"{name}: отсутствует достоверное положительное измерение")
    errors = inventory.get("errors")
    if not isinstance(errors, (list, tuple)):
        reasons.append("inventory errors field is missing or malformed")
        errors = []
    else:
        errors = [str(error) for error in errors]
    reasons.extend(errors)
    for name, measured in required.items():
        snapshot = system.get(name)
        if (_positive_finite(measured) and _positive_finite(snapshot)
                and float(measured) != float(snapshot)):
            reasons.append(f"{name}: profile and system snapshot disagree")
        elif _positive_finite(measured) != _positive_finite(snapshot):
            reasons.append(f"{name}: profile and system snapshot disagree")
    total_ram = required["ram_total_gib"]
    available_ram = required["ram_available_gib"]
    if (_positive_finite(total_ram) and _positive_finite(available_ram)
            and float(available_ram) > float(total_ram)):
        reasons.append("ram_available_gib: available RAM exceeds the measured total")
    return system, measurements, errors, reasons


def _minimum_resource_reasons(measurements: dict) -> list[str]:
    """Apply only explicit operational stop floors, never claim a model budget."""
    reasons = []
    for name, minimum in (
        ("ram_available_gib", _AGENT_MINIMUM_RAM_AVAILABLE_GIB),
        ("disk_free_gib", _AGENT_MINIMUM_DISK_FREE_GIB),
    ):
        value = measurements.get(name)
        if _positive_finite(value) and float(value) < minimum:
            reasons.append(f"{name}: measured {float(value):g} GiB is below the agent safety floor {minimum:g} GiB")
    return reasons


def _adaptive_route(system: dict) -> tuple[dict, str, list[str]]:
    from modules.hit_factory.adaptive import get_adaptive_config

    reasons: list[str] = []
    try:
        adaptive = get_adaptive_config(system=system)
        if not isinstance(adaptive, dict):
            raise TypeError("adaptive selector did not return an object")
        adaptive = dict(adaptive)
    except Exception as exc:  # noqa: BLE001 - no renderer-side guessing
        adaptive = {}
        reasons.append(f"adaptive backend selection failed: {type(exc).__name__}: {exc}")
    if adaptive.get("use_acestep"):
        selected = "ace_step"
        reasons.append("ACE-Step выбран, но его отдельное устройство/память не измерены этим приложением")
    elif adaptive.get("use_musicgen"):
        selected = "musicgen"
        reasons.append("Для фактически выбранного MusicGen-small нет явного RAM/VRAM/disk budget; запуск заблокирован")
    else:
        selected = "procedural_dsp"
    # The independent texture stage otherwise probes hardware again and may
    # load MusicGen despite the safe beat route selected above.
    adaptive["use_texture"] = False
    return adaptive, selected, reasons


def _requested_rvc(recipe: Any, system: dict) -> tuple[dict | None, list[str]]:
    from modules.rvc_manager.infer import preflight_rvc_inference

    reasons: list[str] = []
    if not isinstance(recipe, dict):
        reasons.append("agent recipe is malformed")
        recipe = {}
    if recipe.get("use_texture") is not False:
        reasons.append("MusicGen texture is not explicitly disabled; its engine budget is not established")
    if recipe.get("use_rvc") is not True:
        return None, reasons
    vocal_path = str(recipe.get("own_vocal_wav") or "").strip()
    if not vocal_path:
        return None, reasons + ["RVC requested without an input vocal recording"]
    try:
        source = Path(vocal_path).expanduser()
        if source.is_symlink() or not source.is_file():
            return None, reasons + ["Запрошенная вокальная запись отсутствует, не является обычным файлом или является ссылкой"]
        record = preflight_rvc_inference(system=system)
        if not isinstance(record, dict) or record.get("allowed") is not True:
            if not isinstance(record, dict):
                record = {"schema": 1, "allowed": False,
                          "reasons": ["RVC preflight returned a malformed record"]}
            reasons.extend(str(item) for item in record.get("reasons") or [])
        return record, reasons
    except Exception as exc:  # noqa: BLE001 - explicit RVC request fails closed
        record = {"schema": 1, "allowed": False,
                  "reasons": [f"RVC preflight failed: {type(exc).__name__}: {exc}"]}
        return record, reasons + record["reasons"]


def _preflight_record(inventory: dict, measurements: dict, errors: list[str], selected: str,
                      rvc: dict | None, reasons: list[str]) -> dict:
    reasons = list(dict.fromkeys(reasons))
    can_attempt = not reasons
    return {
        "schema": 1,
        "status": "inventory_only" if can_attempt else "blocked",
        "decision": "continue_unverified" if can_attempt else "refuse",
        "can_attempt": can_attempt,
        "selected_backend": selected,
        "inventory": {"os": inventory.get("os"), "os_release": inventory.get("os_release"),
                       "architecture": inventory.get("architecture"),
                       "measurements": measurements, "errors": errors},
        "resource_budget_status": "not_established" if selected == "procedural_dsp"
        else "not_assessed" if selected == "not_selected" else "missing_for_selected_backend",
        "operational_safety_floors_gib": {
            "ram_available": _AGENT_MINIMUM_RAM_AVAILABLE_GIB,
            "disk_free": _AGENT_MINIMUM_DISK_FREE_GIB,
        },
        "texture_route": {"selected_backend": "disabled", "reason": "MusicGen texture budget not established",
                          "inference_verified": False},
        "rvc": rvc,
        "inference_verified": False,
        "product_profile_accepted": False,
        "reasons": reasons,
        "limitations": [
            "Операционные RAM/disk floors только останавливают заведомо малый ресурс; они не являются бюджетом модели или профилем продукта.",
            "Измерение ресурсов не доказывает достаточность бюджета или успешный inference.",
            "Результат DSP/CPU попытки не подтверждает CUDA, AMD GPU, качество музыки или пение.",
            "Опциональная MusicGen-текстура отключена до утверждения отдельного engine budget.",
            "Полный профиль продукта остаётся непринятым.",
        ],
    }


def preflight_agent_hardware(recipe: dict, output_root: str | Path) -> tuple[dict, dict]:
    """Capture hardware once, refuse bad base resources, then route that snapshot."""
    inventory = _capture_inventory(output_root)
    system, measurements, errors, reasons = _inventory_fields(inventory)
    base_reasons = reasons + _minimum_resource_reasons(measurements)
    if base_reasons:
        # Do not import backend/model stacks or inspect an optional RVC runtime
        # when the basic RAM/disk facts already make this run unsafe.
        adaptive = {"use_acestep": False, "use_musicgen": False, "use_texture": False}
        selected = "not_selected"
        rvc = None
        final_reasons = base_reasons
    else:
        adaptive, selected, route_reasons = _adaptive_route(system)
        rvc, rvc_reasons = _requested_rvc(recipe, system)
        final_reasons = reasons + route_reasons + rvc_reasons
    record = _preflight_record(inventory, measurements, errors, selected, rvc, final_reasons)
    return record, adaptive

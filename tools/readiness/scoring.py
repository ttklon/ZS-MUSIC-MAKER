# -*- coding: utf-8 -*-
"""
tools/readiness/scoring.py — свёртка проб в честный процент готовности.

Потолки (caps) применяются жёстко: без реальной записи с микрофона готовность
не может быть выше 80 %, без тяжёлых движков — выше 65 %.
"""

from __future__ import annotations

import math
from typing import Any

from tools.readiness.inventory import module_inventory_summary
from tools.readiness.paths import STATUS_WEIGHT, WEIGHTS
from tools.readiness.probes import (
    probe_architecture,
    probe_audio_pipeline,
    probe_core_modules,
    probe_release,
    probe_testing,
    probe_voice_recording,
)


def _block_percent(probes: dict[str, str]) -> float:
    if not probes:
        return 0.0
    score = sum(STATUS_WEIGHT.get(v, 0.0) for v in probes.values())
    return round(100.0 * score / len(probes), 2)


def compute() -> tuple[float, dict[str, Any]]:
    blocks_raw = {
        "architecture": probe_architecture(),
        "core_modules": probe_core_modules(),
        "audio_pipeline": probe_audio_pipeline(),
        "voice_recording": probe_voice_recording(),
        "release": probe_release(),
        "testing": probe_testing(),
    }
    block_pcts = {key: _block_percent(value) for key, value in blocks_raw.items()}

    # Достижимость ядра: доля прод-модулей, до которых можно дойти от точек
    # входа. Мёртвый код обязан снижать балл, иначе индикатор снова врёт.
    inventory = module_inventory_summary()
    total_modules = max(1, inventory["tracked_modules"])
    live_share = (
        inventory["REAL_PASS"] + inventory["REAL_FAIL"]
    ) / total_modules
    if "core_modules" in block_pcts:
        block_pcts["core_modules"] = round(block_pcts["core_modules"] * live_share, 2)

    total = 0.0
    for key, weight in WEIGHTS.items():
        total += block_pcts.get(key, 0.0) * weight / 100.0

    caps: list[tuple[float, str]] = []
    if blocks_raw["voice_recording"].get("mic_recording") != "REAL_PASS":
        caps.append((80.0, "no real microphone recording available"))
    heavy = [
        key
        for key in ("musicgen_runtime", "demucs_runtime")
        if blocks_raw["audio_pipeline"].get(key) == "BLOCKED"
    ]
    if heavy:
        caps.append((65.0, f"heavy engines unavailable: {heavy}"))
    if blocks_raw["architecture"].get("updater_module") != "REAL_PASS":
        caps.append((85.0, "no updater module"))

    cap_min = min([cap[0] for cap in caps], default=100.0)
    final = math.floor(min(total, cap_min))

    return float(final), {
        "module_inventory": inventory,
        "module_reachability_share": round(live_share, 4),
        "block_scores": block_pcts,
        "weights": WEIGHTS,
        "raw_probes": blocks_raw,
        "caps_triggered": caps,
        "weighted_sum": round(total, 2),
        "cap_min": cap_min,
        "final_floor": final,
    }

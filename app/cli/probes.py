# -*- coding: utf-8 -*-
"""
app/cli/probes.py — быстрые пробы состояния системы для CLI.
"""

from __future__ import annotations

from app.cli.env import safe_print


def health_snapshot() -> dict:
    try:
        from modules import health

        rep = health.collect()
        safe_print(
            f"[main] health: {rep.verdict}  "
            f"ready={rep.percent_ready}%  "
            f"core_ok={rep.core_ok}"
        )
        safe_print("[main] health assesses dependencies only; models, GPU inference and audio quality are not verified.")
        from app.ai.profiles import measure_profile
        from pathlib import Path
        hardware = measure_profile(Path.cwd())
        safe_print("[main] hardware: " + str(hardware))
        return {"verdict": rep.verdict, "percent": rep.percent_ready, "hardware": hardware}
    except Exception as e:
        safe_print(f"[main] health not available: {e}")
        return {"verdict": "UNKNOWN", "percent": 0}


def entrypoint_snapshot() -> int:
    import json
    from app.core.entrypoints import ENTRYPOINTS
    safe_print(json.dumps({"schema": 1, "entrypoints": ENTRYPOINTS}, ensure_ascii=False, indent=2))
    return 0


def resource_policy_snapshot() -> int:
    import json
    from app.core.resource_policy import resource_inventory
    report = resource_inventory()
    safe_print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["coverage_complete"] else 1

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
        return {"verdict": rep.verdict, "percent": rep.percent_ready}
    except Exception as e:
        safe_print(f"[main] health not available: {e}")
        return {"verdict": "UNKNOWN", "percent": 0}

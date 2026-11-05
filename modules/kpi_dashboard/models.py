# -*- coding: utf-8 -*-
"""
modules/kpi_dashboard/models.py — структуры отчёта KPI.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class DashboardSection:
    title: str
    ok: bool
    percent: int
    lines: list[str] = field(default_factory=list)


@dataclass
class Dashboard:
    generated_at: str = ""
    percent_tz: int = 0
    verdict: str = ""
    sections: list[dict[str, Any]] = field(default_factory=list)
    checklist: list[dict[str, Any]] = field(default_factory=list)
    advice: list[str] = field(default_factory=list)
    persistence: dict[str, Any] = field(default_factory=lambda: {"requested": False, "status": "not_requested"})

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

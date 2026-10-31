# -*- coding: utf-8 -*-
"""
modules/kpi_dashboard — единый KPI-отчёт по требованиям ТЗ.

Читает `data/health.json`, последний прогон мастера, smoke-отчёты и
телеметрию, склеивает в human-readable отчёт с процентом соответствия и
списком «что упало / что делать дальше». Без внешних зависимостей и сети.

Раскладка: `config` (чек-лист), `models`, `sources`, `checklist`, `report`.
"""

from modules.kpi_dashboard.checklist import _tz_percent  # noqa: F401
from modules.kpi_dashboard.config import TZ_CHECKLIST  # noqa: F401
from modules.kpi_dashboard.models import Dashboard, DashboardSection  # noqa: F401
from modules.kpi_dashboard.sources import _filesystem_tz_checks  # noqa: F401
from modules.kpi_dashboard.report import (  # noqa: F401
    build,
    main,
    render_markdown,
    render_text,
)

__all__ = [
    "Dashboard",
    "DashboardSection",
    "build",
    "main",
    "render_markdown",
    "render_text",
]

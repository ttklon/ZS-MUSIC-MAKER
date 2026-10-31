# -*- coding: utf-8 -*-
"""
tools/readiness — честный расчёт готовности проекта.

Складывается из статической матрицы модулей и реальных проб подсистем;
отсутствие зависимости никогда не превращается в успех. Потолки (`caps`)
применяются явно и печатаются в отчёте.

Раскладка: `paths` (корень/веса), `inventory`, `probes`, `scoring`, `cli`.

Запуск: `python -m tools.readiness [--json|--inventory-markdown]`.
"""

from tools.readiness.cli import main  # noqa: F401
from tools.readiness.inventory import (  # noqa: F401
    inventory_markdown,
    module_inventory,
    module_inventory_summary,
    tracked_python_modules,
)
from tools.readiness.paths import INVENTORY_ROOTS, STATUS_WEIGHT, WEIGHTS  # noqa: F401
from tools.readiness.probes import (  # noqa: F401
    probe_architecture,
    probe_audio_pipeline,
    probe_core_modules,
    probe_release,
    probe_testing,
    probe_voice_recording,
)
from tools.readiness.scoring import compute  # noqa: F401

__all__ = [
    "INVENTORY_ROOTS",
    "STATUS_WEIGHT",
    "WEIGHTS",
    "compute",
    "inventory_markdown",
    "main",
    "module_inventory",
    "module_inventory_summary",
    "probe_architecture",
    "probe_audio_pipeline",
    "probe_core_modules",
    "probe_release",
    "probe_testing",
    "probe_voice_recording",
    "tracked_python_modules",
]

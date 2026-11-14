# -*- coding: utf-8 -*-
"""
tools/readiness/paths.py — корень репозитория, охват инвентаря и веса блоков.

`REAL_PASS` в матрице означает «файл парсится и на него есть статическая
ссылка из production или тестов», а НЕ утверждение о реальном inference.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

INVENTORY_ROOTS = ("app", "agents", "config", "modules", "tools", "ui", "updater")
TEST_ROOT = "tests"


WEIGHTS = {
    "architecture": 10,
    "core_modules": 25,
    "audio_pipeline": 25,
    "voice_recording": 20,
    "release": 10,
    "testing": 10,
}

STATUS_WEIGHT = {
    "REAL_PASS": 1.00,
    "PARTIAL": 0.50,
    # Код есть и работает, но из точек входа недостижим: в готовность
    # продукта он не входит, но и «отсутствующим» не считается.
    "DEPRECATED": 0.25,
    "FALLBACK_ONLY": 0.25,
    "MOCK": 0.00,
    "FAILED": 0.00,
    "MISSING": 0.00,
    "NOT_TESTED": 0.00,
    "BLOCKED": 0.00,
}

# -*- coding: utf-8 -*-
"""
modules/beat/paths.py — каталог для готовых битов.

Значение читается с фасада `modules.beat_constructor`, чтобы подмена
`OUTPUT_DIR` (тесты, CI, переменная окружения) работала единообразно.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_OUTPUT_DIR = os.environ.get(
    "ZSMM_BEAT_OUTPUT_DIR",
    str(Path(__file__).resolve().parents[2] / "output" / "beats"),
)


def output_dir() -> str:
    """Актуальный каталог битов (учитывает подмену OUTPUT_DIR на фасаде)."""
    from modules import beat_constructor

    return str(getattr(beat_constructor, "OUTPUT_DIR", DEFAULT_OUTPUT_DIR))

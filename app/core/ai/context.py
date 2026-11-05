# -*- coding: utf-8 -*-
"""app/core/ai/context.py — состояние AI-пайплайна, передаваемое стадиям."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AIContext:
    """Всё, что нужно стадии: рецепт, каталог вывода и флаги запуска.

    Стадии не замыкаются на локальные переменные пайплайна — это позволяло
    держать всю логику внутри одной функции на 470 строк.
    """

    ws: dict[str, Any]
    out_root: Path
    dry_run: bool = False
    artist_slug: str | None = None
    ref_track_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

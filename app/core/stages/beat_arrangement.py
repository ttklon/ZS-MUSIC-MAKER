# -*- coding: utf-8 -*-
"""app/core/stages/beat_arrangement.py — связь плана аранжировки с битом (T6).

Структура трека решается один раз — в аранжировке; бит следует принятому
решению, а не планирует собственную сетку. Флаг
`ZSMM_ARRANGEMENT_DRIVES_BEAT=0` возвращает прежнее поведение бит-в-бит.
"""

from __future__ import annotations

import os
from typing import Any

# Аварийный выход: `ZSMM_ARRANGEMENT_DRIVES_BEAT=0` возвращает прежнее,
# независимое планирование бита (бит-в-бит как до доработки).
ARRANGEMENT_DRIVES_BEAT_ENV = "ZSMM_ARRANGEMENT_DRIVES_BEAT"


def _arrangement_drives_beat() -> bool:
    """Включено ли влияние плана аранжировки на бит (по умолчанию — да)."""
    raw = os.environ.get(ARRANGEMENT_DRIVES_BEAT_ENV, "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def _arrangement_sections(plan: Any) -> tuple[list | None, str | None]:
    """Секции плана аранжировки для конструктора бита.

    Возвращает `(None, причина)`, если влияние выключено флагом или план пуст:
    бит тогда планирует структуру сам, но причина видна в отчёте, а не теряется.
    """
    if not _arrangement_drives_beat():
        return None, None
    sections = (plan or {}).get("sections") if isinstance(plan, dict) else None
    if not sections:
        return None, "no arrangement sections; beat planned its own structure"
    return list(sections), None

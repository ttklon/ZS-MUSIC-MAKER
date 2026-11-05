# -*- coding: utf-8 -*-
"""
app/pipeline — единый контракт стадий и итоговой сводки пайплайна.

Одно место, где определяется, что такое успешная стадия:

    OK       — стадия отработала полностью, без упрощений;
    FALLBACK — отработала, но с явно помеченным упрощением (engine X, причина Y);
    BLOCKED  — тяжёлая зависимость недоступна; стадия честно пропущена,
               обвязка цела (это НЕ успех и НЕ провал);
    FAILED   — стадия сломалась; причина обязательна.

`StageResult` — то, что возвращает стадия; `summarize()` — единственная
функция, которая превращает список стадий в `verdict` + `percent`.
"""

from __future__ import annotations

from app.pipeline.stage import StageResult  # noqa: F401 - публичный реэкспорт
from app.pipeline.stage import StageStatus  # noqa: F401 - публичный реэкспорт
from app.pipeline.stage import classify  # noqa: F401 - публичный реэкспорт
from app.pipeline.stage import summarize  # noqa: F401 - публичный реэкспорт

__all__ = ["StageResult", "StageStatus", "classify", "summarize"]

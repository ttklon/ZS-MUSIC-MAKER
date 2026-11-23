# -*- coding: utf-8 -*-
"""modules/errors.py — одна причина отказа для всего проекта.

Зачем отдельный модуль
----------------------
В отчётах и результатах стадий причина падения почти всегда собиралась как
`str(e)`. Для большинства исключений это работает, но не для всех: у
`audioread.exceptions.NoBackendError` сообщения нет вообще, и `str(e) == ""`.
Итог в `report.json` — `reason: ""`: стадия упала, отчёт это зафиксировал, а
человек не может понять ни что случилось, ни куда смотреть.

Правило: причина отказа никогда не бывает пустой строкой. Минимум — имя типа
исключения. Это дешёвая операция, но именно она отличает «отчёт честный» от
«отчёт формально заполнен».
"""

from __future__ import annotations


def failure_reason(exc: BaseException) -> str:
    """Читаемая причина отказа. Никогда не пустая.

    >>> failure_reason(ValueError("not found: a.wav"))
    'ValueError: not found: a.wav'
    """
    text = str(exc).strip()
    name = type(exc).__name__
    return f"{name}: {text}" if text else name

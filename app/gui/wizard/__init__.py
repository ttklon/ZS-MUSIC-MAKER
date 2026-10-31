# -*- coding: utf-8 -*-
"""
app/gui/wizard — мастер из 9 шагов (PySide6).

    ui              общие элементы: заголовки, разделители, StepBase
    steps_intro     статус моделей, имя артиста, референсы
    steps_creative  пресет, браузер сэмплов, текст, голос
    steps_run       экспертные опции, очередь/ночная пачка, результат
    window          главное окно с навигацией, меню и онбордингом

Публичный вход — `from app.gui.wizard import Wizard`.
"""

from __future__ import annotations

from app.gui.wizard.ui import DIM, H1, H2, HR, StepBase  # noqa: F401 - публичный реэкспорт
from app.gui.wizard.window import Wizard  # noqa: F401 - публичный реэкспорт

__all__ = ["DIM", "H1", "H2", "HR", "StepBase", "Wizard"]

# -*- coding: utf-8 -*-
"""
app/gui/wizard — мастер из пяти шагов (PySide6).

    ui               общие элементы: заголовки, разделители, StepBase
    steps_brief      шаг 1: жанр, тема, артист, длительность, seed
    steps_material   шаг 2: референсы, пресет, режим, свои строчки
    steps_voice      шаг 3: режим вокала, своя запись, караоке, RVC
    steps_tuning     шаг 4: BPM, агрессия, стенды, экспорт, сэмплы
    steps_run        шаг 5: запуск, ночная пачка, прогресс + экран результата
    record_dialog    окно записи голоса
    dialogs          диагностика «AI: модели и пайплайн»
    window           главное окно с навигацией, меню и онбордингом

Публичный вход — `from app.gui.wizard import Wizard`.
"""

from __future__ import annotations

from app.gui.wizard.ui import DIM, H1, H2, HR, StepBase  # noqa: F401 - публичный реэкспорт
from app.gui.wizard.window import Wizard  # noqa: F401 - публичный реэкспорт

__all__ = ["DIM", "H1", "H2", "HR", "StepBase", "Wizard"]

# -*- coding: utf-8 -*-
"""
ZS Music Maker — i18n.py (GOD MODE)
========================================================================
Система интернационализации.
Разделяет логику и текстовые сообщения.
"""

class Translator:
    def __init__(self, lang="ru"):
        self.lang = lang
        self.messages = {
            "ru": {
                "start_pipeline": "Запуск пайплайна для проекта: {}",
                "stage_done": "Стадия {} завершена за {:.2f}с",
                "error_stage": "Ошибка в стадии {}: {}",
                "loading_checkpoint": "Загрузка чекпоинта для стадии: {}",
                "all_ok": "Все жанры валидны и готовы к бою.",
                "gui_error": "[ERROR] GUI не найден. Установите необходимые библиотеки."
            },
            "en": {
                "start_pipeline": "Launching pipeline for project: {}",
                "stage_done": "Stage {} completed in {:.2f}s",
                "error_stage": "Error in stage {}: {}",
                "loading_checkpoint": "Loading checkpoint for stage: {}",
                "all_ok": "All genres are valid and battle-ready.",
                "gui_error": "[ERROR] GUI not found. Please install required libraries."
            }
        }

    def t(self, key, *args):
        msg = self.messages.get(self.lang, self.messages["en"]).get(key, key)
        return msg.format(*args) if args else msg

# Глобальный переводчик
i18n = Translator(lang="ru")

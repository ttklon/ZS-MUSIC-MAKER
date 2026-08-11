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
                "start_pipeline": ">>> Запуск пайплайна для проекта: {}",
                "stage_done": "[OK] Стадия {} завершена за {:.2f}с",
                "error_stage": "[FAIL] Ошибка в стадии {}: {}",
                "loading_checkpoint": "[DISK] Загрузка чекпоинта для стадии: {}",
                "all_ok": "Все жанры валидны и готовы к бою.",
                "gui_error": "[ERROR] GUI не найден. Установите необходимые библиотеки.",
                "sanitizer_warning": "[WARN] Обнаружены некорректные значения (NaN/Inf) в аудио-буфере. Исправлено.",
                "mastering_start": ">>> Запуск мастеринга...",
                "export_success": "[DONE] Экспорт завершен: {}",
                "model_download": "[NET] Загрузка модели: {}",
                "gpu_detected": "[HW] Обнаружен GPU: {}. Используем ускорение.",
                "cpu_fallback": "[HW] GPU не найден. Используем CPU (Fallback).",
                "mem_warning": "[WARN] Низкий объем памяти! Включаем режим экономии."
            },
            "en": {
                "start_pipeline": ">>> Launching pipeline for project: {}",
                "stage_done": "[OK] Stage {} completed in {:.2f}s",
                "error_stage": "[FAIL] Error in stage {}: {}",
                "loading_checkpoint": "[DISK] Loading checkpoint for stage: {}",
                "all_ok": "All genres are valid and battle-ready.",
                "gui_error": "[ERROR] GUI not found. Please install required libraries.",
                "sanitizer_warning": "[WARN] Invalid values (NaN/Inf) detected in audio buffer. Fixed.",
                "mastering_start": ">>> Starting mastering...",
                "export_success": "[DONE] Export completed: {}",
                "model_download": "[NET] Downloading model: {}",
                "gpu_detected": "[HW] GPU detected: {}. Using acceleration.",
                "cpu_fallback": "[HW] GPU not found. Using CPU (Fallback).",
                "mem_warning": "[WARN] Low memory detected! Enabling power-save mode."
            }
        }

    def t(self, key, *args):
        msg = self.messages.get(self.lang, self.messages["en"]).get(key, key)
        try:
            return msg.format(*args) if args else msg
        except:
            return msg

# Глобальный переводчик
i18n = Translator(lang="ru")


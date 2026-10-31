# -*- coding: utf-8 -*-
"""
modules/kpi_dashboard/config.py — корень проекта и чек-лист требований ТЗ,
по которому считается процент соответствия.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Требования ТЗ, по которым считается процент соответствия (см. раздел 16).
TZ_CHECKLIST: list[dict[str, str]] = [
    {"key": "modules_12", "tz": "3.1-3.12", "title": "12 модулей архитектуры"},
    {"key": "gui_wizard", "tz": "5", "title": "Единое окно, мастер по шагам"},
    {"key": "karaoke", "tz": "5", "title": "Караоке-режим для записи"},
    {"key": "onboarding", "tz": "5", "title": "Интерактивный Onboarding"},
    {"key": "utf8_cp866", "tz": "6", "title": "UTF-8 в коде, CP866 в консоли"},
    {"key": "auto_deps", "tz": "6", "title": "Авто-подтяжка зависимостей"},
    {"key": "smoke_tests", "tz": "7", "title": "Smoke + E2E тесты"},
    {
        "key": "readme_context",
        "tz": "8+11",
        # v37 FIX: CONTEXT.md никогда не существовал в репо — канонический
        # накопительный журнал это SESSION_LOG.md (см. правило 11 ТЗ).
        "title": "README + SESSION_LOG.md накопительно",
    },
    {"key": "agents_free", "tz": "9", "title": "Бесплатные интернет-агенты"},
    {"key": "logging", "tz": "11", "title": "Логирование всего в logs/app.log"},
    {"key": "hw_autodetect", "tz": "20.1", "title": "HW autodetect + fallback"},
    {"key": "rvc_real", "tz": "20.1[RVC]", "title": "RVC 100% рабочий"},
    {"key": "musicgen_full", "tz": "20.1[MG]", "title": "MusicGen полноценный на 12GB"},
    {"key": "author_ref", "tz": "20.3", "title": "Автор из референсов / поиск"},
    {"key": "female_backing", "tz": "20.3", "title": "Женские бэки"},
    {"key": "expert_mode", "tz": "20.3", "title": "Экспертный режим (скрытый ⋯)"},
    {
        "key": "license_provenance",
        "tz": "20.3",
        "title": "License / Provenance Manager",
    },
    {"key": "release_full", "tz": "20.2 п.32", "title": "Полный релиз-пакет"},
    {"key": "distribution_5", "tz": "20.2 п.33", "title": "5 платформ дистрибуции"},
    {"key": "hit_scorer", "tz": "20.2 п.34", "title": "AI Detector Pro + hit_scorer"},
    {"key": "queue_5", "tz": "20.2 п.35А", "title": "Очередь ≥5 треков"},
    {"key": "kpi_20_5", "tz": "20.5", "title": "KPI-мониторинг"},
]

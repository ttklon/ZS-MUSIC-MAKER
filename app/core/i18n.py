"""Minimal runtime i18n for user-facing menu and pipeline strings."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "ru": {
        "menu.file": "Файл",
        "menu.settings": "Настройки",
        "menu.help": "Помощь",
        "menu.language": "Язык",
        "menu.tour": "Обучающий тур",
        "menu.about": "О программе",
        "menu.ai": "AI",
        "menu.model_status": "Статус моделей",
        "nav.back": "← Назад",
        "nav.next": "Далее →",
        "nav.help": "❓ Помощь (F1)",
        "pipeline.started": "Пайплайн запущен",
        "pipeline.stage": "Стадия: {stage}",
        "pipeline.completed": "Пайплайн завершён",
        "pipeline.failed": "Пайплайн завершился с ошибкой: {reason}",
        "status.ready": "Готово",
        "status.running": "Выполняется",
        "status.blocked": "Недоступно",
    },
    "en": {
        "menu.file": "File",
        "menu.settings": "Settings",
        "menu.help": "Help",
        "menu.language": "Language",
        "menu.tour": "Guided tour",
        "menu.about": "About",
        "menu.ai": "AI",
        "menu.model_status": "Model status",
        "nav.back": "← Back",
        "nav.next": "Next →",
        "nav.help": "❓ Help (F1)",
        "pipeline.started": "Pipeline started",
        "pipeline.stage": "Stage: {stage}",
        "pipeline.completed": "Pipeline completed",
        "pipeline.failed": "Pipeline failed: {reason}",
        "status.ready": "Ready",
        "status.running": "Running",
        "status.blocked": "Unavailable",
    },
}

@dataclass
class _LanguageState:
    active: str = "ru"


_lock = RLock()
_language_state = _LanguageState()


def available_languages() -> tuple[str, ...]:
    return tuple(_TRANSLATIONS)


def set_language(language: str) -> str:
    """Switch the process-local UI language immediately and return the active code."""
    normalized = str(language or "").lower().split("-", 1)[0]
    if normalized not in _TRANSLATIONS:
        raise ValueError(f"unsupported language: {language}")
    with _lock:
        _language_state.active = normalized
        return _language_state.active


def get_language() -> str:
    with _lock:
        return _language_state.active


def configure_language(language: str | None) -> str:
    """Apply a config value when valid; default remains the currently active language."""
    if language:
        return set_language(language)
    return get_language()


def t(key: str, /, **values: Any) -> str:
    """Translate an allowlisted dotted key; Russian is fallback for missing EN text."""
    with _lock:
        language = _language_state.active
    template = _TRANSLATIONS.get(language, {}).get(key) or _TRANSLATIONS["ru"].get(key) or key
    try:
        return template.format(**values)
    except (KeyError, ValueError):
        return template

# -*- coding: utf-8 -*-
"""
modules.agent_guide.questions — 4 вопроса агентика и их разбор.

Вопросы не «настройки»: каждый ответ меняет прогон, а не украшает форму.
Пустой ответ — это тоже выбор: агент берёт значение из трендов 2026
(`trend_scout`) и говорит об этом в отчёте, а не подставляет константу.
"""

from __future__ import annotations

from typing import Any

# Порядок важен: окно рисует вопросы в этом порядке, ключи — контракт с UI.
QUESTIONS: tuple[dict[str, str], ...] = (
    {
        "id": "mood",
        "label": "1. Настроение / тема — что хочешь спеть?",
        "placeholder": "например: ночной город, тачки, любовь, деньги, движ",
        "hint": "пусто — агент возьмёт актуальную тему из трендов",
    },
    {
        "id": "artist",
        "label": "2. Референс-артист — на кого равняться?",
        "placeholder": "например: ICEGERGERT, LIL PUMP, Скриптонит",
        "hint": "агент соберёт досье: почему популярен, биты, подача, темы",
    },
    {
        "id": "refs",
        "label": "3. Референс-треки — ссылки или wav через запятую",
        "placeholder": "C:\\Music\\ref.wav, https://example.com/ref.mp3",
        "hint": "анализ BPM/тональности/жанра — и жанр выбирается сам",
    },
    {
        "id": "voice",
        "label": "4. Голос — записать сейчас, файл или без вокала",
        "placeholder": "record / путь к wav / пусто",
        "hint": "record = микрофон в окне → RVC (клон твоего голоса)",
    },
)

# Что окно/мост может прислать в payload. Всё остальное игнорируется: свободный
# словарь в скрипт пайплайна — это способ уронить прогон «странным» ключом.
_ALIASES = {
    "mood": ("mood", "theme", "настроение"),
    "artist": ("artist", "artist_slug", "refference_artist"),
    "refs": ("refs", "references", "ref_tracks"),
    "voice": ("voice", "voice_path", "vocal"),
}

VOICE_MODES = ("record", "file", "none")


def _first(payload: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return ""


def _as_list(value: Any) -> list[str]:
    """Референсы приходят строкой через запятую или готовым списком."""
    if isinstance(value, (list, tuple, set)):
        items = [str(item).strip() for item in value]
    else:
        items = [part.strip() for part in str(value or "").replace(";", ",").split(",")]
    return [item for item in items if item]


def _voice(value: Any) -> dict[str, Any]:
    """Голос: `record`, путь к файлу или «нет вокала». Больше вариантов нет."""
    text = str(value or "").strip()
    lowered = text.lower()
    if lowered in ("record", "запись", "микрофон", "mic", "1"):
        return {"mode": "record", "path": ""}
    if lowered in ("", "none", "no", "без", "нет", "-"):
        return {"mode": "none", "path": ""}
    return {"mode": "file", "path": text}


def parse_answers(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Ответы пользователя → нормализованный словарь без сюрпризов.

    Возвращает ровно четыре ключа (`mood`, `artist`, `refs`, `voice`).
    Строки обрезаются до разумной длины: тема из 4000 символов не станет
    лучше, но сломает промпт и имя каталога.
    """
    data = payload if isinstance(payload, dict) else {}
    mood = " ".join(str(_first(data, _ALIASES["mood"]) or "").split())[:300]
    artist = " ".join(str(_first(data, _ALIASES["artist"]) or "").split())[:80]
    refs = _as_list(_first(data, _ALIASES["refs"]))
    return {
        "mood": mood,
        "artist": artist,
        "refs": refs[:7],
        "voice": _voice(_first(data, _ALIASES["voice"])),
    }


def answer_summary(answers: dict[str, Any]) -> str:
    """Одна строка «что понял агент» — для окна и для лога прогона."""
    voice = (answers.get("voice") or {}).get("mode") or "none"
    voice_text = {"record": "микрофон → RVC", "file": "файл → RVC", "none": "без вокала"}[
        voice if voice in VOICE_MODES else "none"
    ]
    return (
        f"тема={answers.get('mood') or 'из трендов'}; "
        f"артист={answers.get('artist') or 'из трендов'}; "
        f"референсы={len(answers.get('refs') or [])}; голос={voice_text}"
    )

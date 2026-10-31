# -*- coding: utf-8 -*-
"""
modules/beat/patterns.py — ритмические пресеты бита (16 шагов на такт).

Пять слотов (kick/snare/hat/bass/melody) на жанр. Пресет переопределяется
groove-шаблоном; `slot_preset_for_genre` всегда возвращает полный набор
слотов, чтобы бит не собирался «наполовину».
"""

from __future__ import annotations

SLOT_NAMES = ("kick", "snare", "hat", "bass", "melody")


GENRE_SLOT_PRESETS = {
    "phonk": {
        "kick": [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hat": [1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1],
        "bass": [1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
        "melody": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    },
    "trap": {
        "kick": [1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hat": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "bass": [1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0],
        "melody": [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
    },
    "house": {
        "kick": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hat": [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
        "bass": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        "melody": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    },
}


LEGACY_SLOT_PRESET = {
    "kick": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    "hat": [0] * 16,
    "bass": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    "melody": [0] * 16,
}


def slot_preset_for_genre(genre: str | None) -> dict[str, list[int]]:
    """Return a copy of a complete 16-step preset for the requested genre."""
    normalized = (genre or "").lower()
    selected = "phonk" if "phonk" in normalized or "drift" in normalized else "trap" if "trap" in normalized or "hip" in normalized else "house" if "house" in normalized or "techno" in normalized else "phonk"
    return {slot: list(values) for slot, values in GENRE_SLOT_PRESETS[selected].items()}

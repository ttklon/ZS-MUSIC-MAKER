# -*- coding: utf-8 -*-
"""
modules/beat_constructor.py — публичный вход конструктора бита.

Реализация разложена по ответственностям в `modules/beat/`:

    patterns     ритмические пресеты по жанрам
    samples      классификация и загрузка сэмплов
    voices       синтез kick/snare/hat/bass/melody/fx
    arrangement  сборка секции из тактов
    constructor  состояние, RNG, запись WAV
    paths        каталог вывода

Здесь остаётся контракт: `BeatConstructor`, `construct_beat`, пресеты и
`OUTPUT_DIR` (его подменяют тесты и переменная `ZSMM_BEAT_OUTPUT_DIR`).
"""

from __future__ import annotations

from modules.beat.constructor import BeatConstructor
from modules.beat.paths import DEFAULT_OUTPUT_DIR, output_dir  # noqa: F401 - публичный реэкспорт
from modules.beat.patterns import (  # noqa: F401 - публичный реэкспорт
    GENRE_SLOT_PRESETS,
    family_for_genre,
    families,
    velocity_map_for_genre,
)
from modules.beat.patterns import LEGACY_SLOT_PRESET  # noqa: F401 - публичный реэкспорт
from modules.beat.patterns import SLOT_NAMES  # noqa: F401 - публичный реэкспорт
from modules.beat.patterns import slot_preset_for_genre  # noqa: F401 - публичный реэкспорт

OUTPUT_DIR = DEFAULT_OUTPUT_DIR

__all__ = [
    "BeatConstructor",
    "GENRE_SLOT_PRESETS",
    "LEGACY_SLOT_PRESET",
    "OUTPUT_DIR",
    "SLOT_NAMES",
    "construct_beat",
    "family_for_genre",
    "families",
    "output_dir",
    "slot_preset_for_genre",
    "velocity_map_for_genre",
]


def construct_beat(
    groove: dict,
    samples: list,
    style_vector: dict,
    duration_sec: int = 120,
    n_verses: int = 2,
    aggression: float = 0.7,
    out_name: str = "constructed_beat.wav",
) -> dict:
    """Удобная функция-обёртка для вызова из main.py."""
    bpm = style_vector.get("target_bpm", 128)
    mode = style_vector.get("target_mode", "minor")
    key_root = style_vector.get("key_root") or "A"
    if not style_vector.get("key_root"):
        for ind in style_vector.get("individual", []):
            key_root = ind.get("key_root") or key_root
            break
    key = f"{key_root} {mode}"

    bc = BeatConstructor(
        bpm=bpm,
        key=key,
        groove=groove,
        samples=samples,
        genre=str(style_vector.get("genre") or style_vector.get("style") or "phonk"),
        seed=style_vector.get("seed"),
    )
    return bc.build_track(
        duration_sec=duration_sec,
        n_verses=n_verses,
        aggression=aggression,
        out_name=out_name,
    )


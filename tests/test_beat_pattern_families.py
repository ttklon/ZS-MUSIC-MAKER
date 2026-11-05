# -*- coding: utf-8 -*-
"""
Гейты ритмических семейств: каждый жанр каталога получает осмысленный грув,
семейства не копируют друг друга, акценты не вырождаются в константу.
"""

from __future__ import annotations

import json
from pathlib import Path

from modules.beat import patterns
from modules.beat_constructor import BeatConstructor, family_for_genre, velocity_map_for_genre

PRESETS = Path(__file__).resolve().parents[1] / "data" / "genre_presets"


def test_every_catalog_genre_maps_to_a_known_family() -> None:
    names = sorted(path.stem for path in PRESETS.glob("*.json"))
    assert len(names) >= 40, f"каталог жанров подозрительно мал: {len(names)}"

    mapped = {name: family_for_genre(name) for name in names}
    unknown = {name: family for name, family in mapped.items() if family not in patterns.families()}

    assert not unknown, f"жанры без семейства: {unknown}"
    assert len(set(mapped.values())) >= 8, f"слишком мало семейств: {set(mapped.values())}"


def test_families_are_structurally_complete_and_distinct() -> None:
    families = patterns.families()
    assert len(families) >= 12

    for family in families:
        preset = patterns.PATTERN_FAMILIES[family]
        assert tuple(preset) == patterns.SLOT_NAMES
        assert all(len(steps) == 16 for steps in preset.values()), family
        assert sum(preset["kick"]) >= 2, f"{family}: без бочки грува нет"
        assert sum(preset["snare"]) >= 1, f"{family}: нет малого"
        assert preset["kick"] != preset["bass"], f"{family}: бас копирует бочку"

    signatures = {
        family: tuple(tuple(steps) for steps in patterns.PATTERN_FAMILIES[family].values())
        for family in families
    }
    assert len(set(signatures.values())) == len(families), "семейства дублируют друг друга"


def test_velocity_maps_are_accented_not_flat() -> None:
    for family in patterns.families():
        mapping = velocity_map_for_genre(family)
        assert tuple(mapping) == patterns.SLOT_NAMES
        for slot, values in mapping.items():
            assert len(values) == 16, f"{family}/{slot}"
            assert all(0.4 <= value <= 1.3 for value in values), f"{family}/{slot}: {values}"
        assert len(set(mapping["hat"])) >= 3, f"{family}: хэт звучит ровной лентой"


def test_constructor_uses_family_velocity_and_reports_family() -> None:
    phonk = BeatConstructor(bpm=128, genre="drift phonk", groove={}, seed=1)
    house = BeatConstructor(bpm=124, genre="tech house", groove={}, seed=1)

    assert phonk.velocity_map["kick"] != house.velocity_map["kick"]
    assert phonk.slot_patterns["hat"] != house.slot_patterns["hat"]


def test_groove_pattern_override_still_wins_over_family() -> None:
    override = [1] + [0] * 15
    constructor = BeatConstructor(genre="amapiano", groove={"kick_pattern": override})

    assert constructor.slot_patterns["kick"] == override


def test_legacy_genre_keeps_flat_velocity_and_empty_hat() -> None:
    legacy = BeatConstructor(genre="legacy", groove={})

    assert set(legacy.velocity_map["hat"]) == {1.0}
    assert sum(legacy.slot_patterns["hat"]) == 0


def test_family_summary_is_serialisable_for_reports() -> None:
    summary = patterns.family_summary()

    assert summary and all({"family", "density", "accents"} <= set(row) for row in summary)
    json.dumps(summary)

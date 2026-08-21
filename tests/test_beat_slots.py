from __future__ import annotations

import time

import numpy as np

from modules.beat_constructor import SLOT_NAMES, BeatConstructor, slot_preset_for_genre
from modules.midi_generator import MIDIGenerator, slot_events_for_genre


def test_genre_slot_presets_are_complete_and_distinct() -> None:
    phonk = slot_preset_for_genre("drift phonk")
    trap = slot_preset_for_genre("trap")

    assert tuple(phonk) == SLOT_NAMES
    assert all(len(pattern) == 16 for pattern in phonk.values())
    assert {tuple(pattern) for pattern in phonk.values()} != {tuple(pattern) for pattern in trap.values()}
    assert phonk["kick"] != phonk["bass"]


def test_constructor_exposes_eight_bar_five_slot_plan_and_honors_override() -> None:
    override = [1] + [0] * 15
    constructor = BeatConstructor(genre="trap", groove={"kick_pattern": override})

    plan = constructor.build_slot_plan(bars=8)

    assert tuple(plan) == SLOT_NAMES
    assert all(len(steps) == 128 for steps in plan.values())
    assert plan["kick"][:16] == override
    assert sum(plan["melody"]) > 0


def test_eight_bar_classic_beat_renders_within_five_seconds() -> None:
    np.random.seed(83)
    constructor = BeatConstructor(bpm=130, genre="phonk", groove={"hihat_density": 0.0})

    started = time.monotonic()
    audio = constructor._build_section("verse", n_bars=8)
    elapsed = time.monotonic() - started

    assert audio.ndim == 2 and audio.shape[1] == 2
    assert len(audio) == int(constructor.sr * (60.0 / 130) * 4) * 8
    assert elapsed < 5.0


def test_five_slot_midi_export_exposes_events_or_honest_blocked(tmp_path) -> None:
    events = slot_events_for_genre("phonk", bars=8)
    result = MIDIGenerator(output_dir=str(tmp_path)).export_slot_pattern("phonk", bpm=130, bars=8)

    assert tuple(events) == SLOT_NAMES
    assert all(len(steps) == 128 for steps in events.values())
    assert result["events"] == events
    if result["ok"]:
        assert result["status"] == "REAL_PASS"
        assert set(result["slots"]) == set(SLOT_NAMES)
    else:
        assert result["status"] == "BLOCKED"
        assert "mido not installed" in result["reason"]

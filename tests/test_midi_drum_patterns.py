from __future__ import annotations

import modules.midi_generator as midi


def test_drum_events_preserve_techno_four_on_floor_and_hat_steps() -> None:
    events = midi.MIDIGenerator._drum_events("techno")

    assert len(events) == 16
    assert [events[index] for index in (0, 4, 8, 12)] == [(36, 110)] * 4
    assert all(events[index] == (42, 78) for index in (1, 2, 3, 5, 15))


def test_drum_events_preserve_phonk_kick_snare_and_cowbell_positions() -> None:
    events = midi.MIDIGenerator._drum_events("drift phonk")

    assert events[0] == events[6] == events[10] == (36, 118)
    assert events[4] == events[12] == (38, 100)
    assert events[8] == (56, 90)
    assert events[1] == (42, 70)


def test_drum_events_keep_default_hat_velocity_in_expected_range(monkeypatch) -> None:
    monkeypatch.setattr(midi.random, "randint", lambda lower, upper: upper)

    events = midi.MIDIGenerator._drum_events("pop-rock")

    assert events[0] == events[8] == (36, 108)
    assert events[4] == events[12] == (38, 102)
    assert events[1] == (42, 90)

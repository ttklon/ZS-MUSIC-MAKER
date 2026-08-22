from __future__ import annotations

import numpy as np

import modules.groove_extractor as groove


def test_step_envelopes_preserve_frame_grouping() -> None:
    kick, snare, hihat = groove._step_envelopes(
        np.array([1.0, 3.0, 5.0, 7.0]),
        np.array([2.0, 4.0, 6.0, 8.0]),
        np.array([4.0, 8.0, 12.0, 16.0]),
        frames_per_step=2,
        max_steps=3,
    )

    assert kick == [2.0, 6.0]
    assert snare == [3.0, 7.0]
    assert hihat == [6.0, 14.0]


def test_groove_metric_helpers_preserve_rhythm_signals() -> None:
    steps_per_bar = 4
    kick_steps = [1.0, 2.0, 1.0, 2.0, 4.0, 8.0, 4.0, 8.0]
    kick_binary = [1, 1, 0, 0, 1, 0, 0, 1]

    assert groove._swing_value(kick_steps, steps_per_bar) > 0
    assert groove._has_triplet_rolls(kick_binary, steps_per_bar) is True
    assert groove._pattern_changes(kick_binary, steps_per_bar, bar_sec=2.5) == [
        {"bar": 1, "time_sec": 2.5}
    ]
    assert groove._drop_intensity(kick_steps, steps_per_bar) > 0

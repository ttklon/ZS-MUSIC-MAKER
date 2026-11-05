# -*- coding: utf-8 -*-
"""
Гейты гармонии бита: прогрессии диатоничны, голосоведение плавное.

Без этих проверок «гармония» легко превращается в случайные аккорды,
которые звучат фальшиво на слух, но проходят любые smoke-тесты.
"""

from __future__ import annotations

import numpy as np

from modules.beat import harmony
from modules.beat_constructor import BeatConstructor


def test_progression_is_chosen_by_genre_and_seed() -> None:
    assert harmony.progression_for("drift phonk", 0) == harmony.PROGRESSIONS["phonk"][0]
    assert harmony.progression_for("drift phonk", 1) == harmony.PROGRESSIONS["phonk"][1]
    assert harmony.progression_for("deep house", 0) == harmony.PROGRESSIONS["house"][0]
    assert harmony.progression_for("unknown genre", 0) == harmony.PROGRESSIONS["default"][0]
    assert all(0 <= degree <= 6 for degree in harmony.progression_for("trap", 0))


def test_chord_freqs_are_diatonic_minor_thirds() -> None:
    root = 110.0
    tonic = harmony.chord_freqs(root, 0, minor=True)
    subdominant = harmony.chord_freqs(root, 3, minor=True)

    assert tonic == [110.0, 130.81, 164.81] or abs(tonic[1] - 130.81) < 0.05
    assert abs(subdominant[0] - 146.83) < 0.05, "iv ступень обязана быть квартой от тоники"
    assert all(low < high for low, high in zip(tonic, tonic[1:]))


def test_seventh_chord_adds_a_fourth_voice() -> None:
    triad = harmony.chord_freqs(110.0, 0, seventh=False)
    seventh = harmony.chord_freqs(110.0, 0, seventh=True)

    assert len(triad) == 3
    assert len(seventh) == 4
    assert seventh[-1] > triad[-1]


def test_voice_leading_moves_voices_by_small_intervals() -> None:
    root = 110.0
    previous = harmony.chord_freqs(root, 0)
    led = harmony.voice_lead(harmony.chord_freqs(root, 5), previous)

    movements = [abs(12.0 * np.log2(new / old)) for new, old in zip(led, previous)]
    assert len(led) == 3
    assert max(movements) <= 5.0, f"голоса скачут на {max(movements):.1f} полутонов"


def test_voice_leading_keeps_register_inside_bass_free_zone() -> None:
    led = harmony.voice_lead(harmony.chord_freqs(55.0, 6), harmony.chord_freqs(55.0, 2))

    assert all(freq >= 60.0 for freq in led)
    assert max(led) <= 55.0 * 8.0


def test_pad_and_keys_are_bounded_and_not_silent() -> None:
    sr = 44_100
    chord = harmony.chord_freqs(110.0, 0)
    pad = harmony.synth_pad(sr, chord, 1.0)
    keys = harmony.synth_keys(sr, chord, 0.4)

    for signal in (pad, keys):
        assert signal.dtype == np.float32
        assert np.max(np.abs(signal)) > 0.5
        assert np.max(np.abs(signal)) <= 1.0


def test_pad_energy_sits_in_the_mid_band_not_in_the_air() -> None:
    sr = 44_100
    pad = harmony.synth_pad(sr, harmony.chord_freqs(110.0, 0), 1.0).astype(np.float64)
    spectrum = np.abs(np.fft.rfft(pad))
    freqs = np.fft.rfftfreq(len(pad), 1.0 / sr)
    total = spectrum.sum()
    mid = spectrum[(freqs >= 80.0) & (freqs <= 2500.0)].sum() / total
    air = spectrum[freqs >= 9000.0].sum() / total

    assert mid >= 0.6, f"пэд обязан жить в середине, доля = {mid:.2f}"
    assert air <= 0.2, f"пэд не должен шипеть, доля ВЧ = {air:.2f}"


def test_progression_follows_the_song_and_repeats_per_four_bars() -> None:
    np.random.seed(11)
    constructor = BeatConstructor(bpm=130, genre="phonk", groove={"hihat_density": 0.0}, seed=0)

    chords = [constructor._chord_for_bar(bar) for bar in range(8)]

    assert [round(freq, 2) for freq in chords[0]] == [round(freq, 2) for freq in chords[4]]
    assert round(chords[1][0], 2) != round(chords[0][0], 2)
    assert len(constructor._generate_harmony(0, "hook", 4096)) == 4096

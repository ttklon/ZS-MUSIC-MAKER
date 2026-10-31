# -*- coding: utf-8 -*-
"""
Гейты качества бита: человеческий микротайминг, спектральный баланс, крест.

Это не «тесты на существование функций», а числовые пороги на то, что
слышно: барабаны не сидят на сетке, у каждого инструмента свой диапазон,
а микс не раздавлен и не перегрет.
"""

from __future__ import annotations

import random

import numpy as np

from modules.beat import drums, humanize
from modules.beat_constructor import BeatConstructor


def _uniform_from(seed: int):
    rng = random.Random(seed)
    return rng.random, rng.uniform


def test_humanize_offsets_are_deterministic_bounded_and_not_identical() -> None:
    random_a, uniform_a = _uniform_from(1)
    random_b, uniform_b = _uniform_from(2)

    offsets_a = [humanize.timing_offset_ms(uniform_a, "snare", step, 0) for step in range(16)]
    offsets_a_again = []
    random_c, uniform_c = _uniform_from(1)
    offsets_a_again = [
        humanize.timing_offset_ms(uniform_c, "snare", step, 0) for step in range(16)
    ]
    offsets_b = [humanize.timing_offset_ms(uniform_b, "snare", step, 0) for step in range(16)]

    assert offsets_a == offsets_a_again, "одинаковый seed обязан давать тот же тайминг"
    assert offsets_a != offsets_b, "разные seed не должны давать идентичный грув"
    assert all(1.0 <= offset <= 8.0 for offset in offsets_a), offsets_a
    assert len(set(offsets_a)) > 8, "смещения не должны быть квантованы в одно значение"


def test_swing_pushes_odd_sixteenths_later() -> None:
    _, uniform_straight = _uniform_from(3)
    _, uniform_swing = _uniform_from(3)

    straight = humanize.timing_offset_ms(uniform_straight, "hat", 1, 0, swing=0.0)
    swung = humanize.timing_offset_ms(uniform_swing, "hat", 1, 0, swing=0.2, step_ms=115.0)

    assert swung > straight, "свинг обязан оттягивать нечётные шестнадцатые назад"


def test_velocity_gain_stays_in_human_range_and_accents_exist() -> None:
    random_a, uniform_a = _uniform_from(5)
    gains = [
        humanize.velocity_gain(random_a, uniform_a, "hat", step, 0) for step in range(16)
    ]

    assert all(0.55 <= gain <= 1.35 for gain in gains), gains
    assert len(set(round(gain, 3) for gain in gains)) > 6
    assert humanize.velocity_gain(random_a, uniform_a, "snare", 8, 0, ghost=True) <= 0.35


def test_synth_kick_energy_sits_in_the_sub_band() -> None:
    sr = 44_100
    kick = drums.synth_kick(sr, np.random.default_rng(1))
    spectrum = np.abs(np.fft.rfft(kick.astype(np.float64)))
    freqs = np.fft.rfftfreq(len(kick), 1.0 / sr)
    sub_share = float(spectrum[freqs <= 120.0].sum() / max(spectrum.sum(), 1e-12))

    assert np.max(np.abs(kick)) > 0.9
    assert sub_share >= 0.48, f"кик обязан держать низ; доля <120 Гц = {sub_share:.2f}"
    assert len(kick) / sr <= 0.9, "кик не должен тянуться бесконечно и съедать грув"


def test_synth_hat_is_bright_and_short() -> None:
    sr = 44_100
    hat = drums.synth_hat(sr, np.random.default_rng(2))
    spectrum = np.abs(np.fft.rfft(hat.astype(np.float64)))
    freqs = np.fft.rfftfreq(len(hat), 1.0 / sr)
    centroid = float((freqs * spectrum).sum() / max(spectrum.sum(), 1e-12))

    assert centroid >= 6000.0, f"хэт обязан быть ярким; центроид = {centroid:.0f} Гц"
    assert len(hat) / sr <= 0.30
    assert np.max(np.abs(hat)) > 0.9


def test_synth_snare_is_broadband_not_a_pure_tone() -> None:
    sr = 44_100
    snare = drums.synth_snare(sr, np.random.default_rng(3))
    spectrum = np.abs(np.fft.rfft(snare.astype(np.float64)))
    freqs = np.fft.rfftfreq(len(snare), 1.0 / sr)
    centroid = float((freqs * spectrum).sum() / max(spectrum.sum(), 1e-12))

    assert 900.0 <= centroid <= 9000.0, f"центроид снейра = {centroid:.0f} Гц"
    assert spectrum[freqs <= 400.0].sum() > 0, "у снейра обязан быть корпус"


def test_rendered_kick_hits_are_off_the_grid_but_tight() -> None:
    np.random.seed(7)
    random.seed(7)
    constructor = BeatConstructor(bpm=130, genre="trap", groove={"hihat_density": 0.0}, seed=11)
    constructor.slot_patterns = {
        "kick": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        "snare": [0] * 16,
        "hat": [0] * 16,
        "bass": [0] * 16,
        "melody": [0] * 16,
    }

    audio = constructor._build_section("verse", 4)[:, 0]
    bar_samples = len(audio) // 4
    step_samples = bar_samples // 16
    derivative = np.abs(np.diff(audio))

    deviations_ms = []
    for bar in range(4):
        for step in (0, 8):
            grid = bar * bar_samples + step * step_samples
            low = max(0, grid - int(0.010 * constructor.sr))
            high = min(len(derivative), grid + int(0.010 * constructor.sr))
            onset = low + int(np.argmax(derivative[low:high]))
            deviations_ms.append((onset - grid) / constructor.sr * 1000.0)

    assert all(abs(dev) <= 9.5 for dev in deviations_ms), deviations_ms
    assert np.mean(np.abs(deviations_ms)) >= 0.3, "кик стоит ровно на сетке — это машина"
    assert np.std(deviations_ms) >= 0.2, "смещения одинаковые — нет живого грува"


def test_rendered_beat_has_healthy_crest_and_no_clipping() -> None:
    np.random.seed(20260822)
    random.seed(20260822)
    constructor = BeatConstructor(bpm=130, groove={"hihat_density": 0.8, "swing": 0.1})

    audio = constructor._build_section("hook", 4)
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(np.square(audio))))
    crest_db = 20.0 * np.log10(peak / max(rms, 1e-12))

    assert peak <= 1.0, "секция не должна клиппировать"
    assert 6.0 <= crest_db <= 22.0, f"крест {crest_db:.1f} дБ вне музыкального диапазона"
    assert audio.ndim == 2 and audio.shape[1] == 2


def test_round_robin_variants_are_bounded_and_varied() -> None:
    random_a, _ = _uniform_from(9)
    picks = [humanize.variant_index(random_a, 4) for _ in range(32)]

    assert all(0 <= pick <= 3 for pick in picks)
    assert len(set(picks)) >= 3, "round-robin обязан перебирать варианты, а не залипать"
    assert humanize.variant_index(random_a, 1) == 0

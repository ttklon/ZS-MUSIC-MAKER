"""Гейты измерительного слоя: true-peak, корреляция, crest, опорное окно."""

from __future__ import annotations

import numpy as np
from scipy.signal import resample_poly

from modules.dsp import metrics


def _stereo(x: np.ndarray) -> np.ndarray:
    return np.stack([x, x], axis=1)


def test_true_peak_matches_full_oversampling():
    sample_rate = 44_100
    time = np.arange(sample_rate) / sample_rate
    for signal in (
        0.5 * np.sin(2 * np.pi * 997 * time),
        np.sign(np.sin(2 * np.pi * 100 * time)) * 0.3,
        np.random.default_rng(7).normal(0, 0.2, sample_rate),
    ):
        audio = _stereo(signal)
        full = 20 * np.log10(np.max(np.abs(resample_poly(audio, 4, 1, axis=0))) + 1e-12)
        assert abs(metrics.true_peak_dbtp(audio) - full) < 0.02


def test_true_peak_never_below_sample_peak():
    audio = _stereo(0.5 * np.sin(2 * np.pi * 1000 * np.arange(16_000) / 16_000))
    assert metrics.true_peak_dbtp(audio) >= metrics.peak_dbfs(audio) - 1e-6


def test_correlation_extremes():
    left = np.sin(2 * np.pi * 200 * np.arange(20_000) / 16_000)
    assert metrics.stereo_correlation(np.stack([left, left], axis=1)) > 0.999
    assert metrics.stereo_correlation(np.stack([left, -left], axis=1)) < -0.999
    mono = metrics.stereo_correlation(left)
    assert mono == 1.0


def test_mono_loss_is_zero_for_identical_channels():
    left = np.random.default_rng(3).normal(0, 0.1, 8_000)
    assert abs(metrics.mono_loss_db(np.stack([left, left], axis=1))) < 0.01


def test_crest_of_sine_is_three_db():
    sine = _stereo(0.5 * np.sin(2 * np.pi * 440 * np.arange(44_100) / 44_100))
    assert 2.9 <= metrics.crest_db(sine) <= 3.1


def test_active_window_picks_the_loud_part():
    sample_rate = 1_000
    quiet = np.full((sample_rate * 3, 2), 0.001)
    loud = np.full((sample_rate * 3, 2), 0.5)
    audio = np.concatenate([quiet, loud, quiet])

    window = metrics.active_window(audio, sample_rate, window_sec=1.0)

    assert metrics.rms_dbfs(window) == metrics.rms_dbfs(loud)
    assert metrics.rms_dbfs(window) > metrics.rms_dbfs(audio) + 4


def test_clipping_samples_counts_only_true_fullscale():
    audio = _stereo(np.array([0.2, 0.99, 1.0, -1.0, 0.5]))
    # два кадра × два канала = 4 сэмпла на потолке
    assert metrics.clipping_samples(audio) == 4


def test_silence_returns_finite_floor_not_minus_infinity():
    silence = np.zeros((4_800, 2))
    assert metrics.rms_dbfs(silence) == metrics.MONO_FLOOR_DB
    assert np.isfinite(metrics.crest_db(silence))

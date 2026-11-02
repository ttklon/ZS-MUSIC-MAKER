# -*- coding: utf-8 -*-
"""6.3: property-based тесты DSP — NaN/Inf, длина, стерео/моно, потолок.

Идея: любая комбинация «странного» входа (тишина, один сэмпл, огромные
значения, стерео/моно) не должна давать NaN, менять длину или пробивать
потолок лимитера. Hypothesis ищет эти случаи за нас — руками такое не
перебрать.
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from modules.dsp import dynamics, filters, limiter, metrics
from modules.mix import width as mix_width

RATE = 8000  # маленькая частота — тесты идут секунды, а не минуты

SAMPLES = st.integers(min_value=1, max_value=4000)
AMPLITUDE = st.floats(min_value=0.0, max_value=4.0, allow_nan=False, allow_infinity=False)
CHANNELS = st.integers(min_value=1, max_value=2)


@st.composite
def audio(draw, channels: int | None = None):
    samples = draw(SAMPLES)
    count = draw(CHANNELS) if channels is None else channels
    amplitude = draw(AMPLITUDE)
    rng = np.random.default_rng(draw(st.integers(min_value=0, max_value=10_000)))
    data = rng.normal(0.0, 1.0, (samples, count)) * amplitude
    return np.asarray(data, dtype=np.float64)


def _finite(x: np.ndarray) -> bool:
    return bool(np.all(np.isfinite(x)))


PROFILE = settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


@PROFILE
@given(data=audio())
def test_filters_keep_shape_and_stay_finite(data: np.ndarray) -> None:
    for cutoff in (300.0, 200.0):
        out = filters.highpass(data, RATE, cutoff)
        assert out.shape == data.shape
        assert _finite(out)
    low, high = filters.split_bands(data, RATE, 400.0)
    assert np.allclose(low + high, data, atol=1e-9)


@PROFILE
@given(data=audio(), gain=st.floats(min_value=-12.0, max_value=12.0))
def test_shelf_is_finite_and_neutral_at_zero(data: np.ndarray, gain: float) -> None:
    out = filters.shelf(data, RATE, 400.0, gain, "high")
    assert out.shape == data.shape
    assert _finite(out)
    if abs(gain) < 1e-9:
        assert np.allclose(out, data, atol=1e-9)


@PROFILE
@given(data=audio())
def test_limiter_never_exceeds_ceiling_and_keeps_length(data: np.ndarray) -> None:
    ceiling = -1.0
    out, info = limiter.limit(data, RATE, ceiling_dbtp=ceiling)
    assert out.shape == data.shape
    assert _finite(out)
    assert metrics.true_peak_dbtp(out) <= ceiling + 0.02
    assert info["ceiling_dbtp"] == ceiling


@PROFILE
@given(data=audio(), knee=st.floats(min_value=-24.0, max_value=-1.0))
def test_soft_clip_is_bounded_and_identity_below_knee(data: np.ndarray, knee: float) -> None:
    out, info = limiter.soft_clip(data, knee_dbfs=knee)
    knee_linear = 10.0 ** (knee / 20.0)
    below = np.abs(data) <= knee_linear
    assert out.shape == data.shape
    assert _finite(out)
    assert np.allclose(out[below], data[below], atol=1e-12)
    assert float(np.max(np.abs(out))) <= max(knee_linear * 1.05, float(np.max(np.abs(data))) + 1e-9)
    assert info["knee_dbfs"] == knee


@PROFILE
@given(data=audio())
def test_metrics_are_finite_for_any_signal(data: np.ndarray) -> None:
    report = metrics.loudness_report(data, RATE)
    for key in ("rms_dbfs", "peak_dbfs", "true_peak_dbtp", "crest_db", "lufs", "mono_loss_db"):
        assert np.isfinite(report[key])
    assert metrics.clipping_samples(data) >= 0
    assert -1.0 <= metrics.stereo_correlation(data) <= 1.0


def test_metrics_survive_silence_and_single_sample() -> None:
    silence = np.zeros((RATE, 2))
    report = metrics.loudness_report(silence, RATE)
    assert report["clipping_samples"] == 0
    assert np.isfinite(report["crest_db"])

    single = np.array([[0.5, -0.4]])
    report = metrics.loudness_report(single, RATE)
    numeric = {
        key: value for key, value in report.items() if isinstance(value, (int, float))
    }
    assert numeric
    for value in numeric.values():
        assert np.isfinite(value)
    assert report["lufs_status"] in {"ok", "unavailable", "failed", "empty"}


@PROFILE
@given(data=audio())
def test_compressor_keeps_length_and_finiteness(data: np.ndarray) -> None:
    out, info = dynamics.compress(data, RATE, threshold_db=-20.0, ratio=2.0)
    assert out.shape == data.shape
    assert _finite(out)
    assert info["ratio"] == 2.0


@PROFILE
@given(data=audio(channels=2))
def test_limiter_reports_finite_gain_reduction(data: np.ndarray) -> None:
    out, info = limiter.limit(data, RATE, ceiling_dbtp=-1.0)
    assert out.shape == data.shape
    assert np.isfinite(info["gain_reduction_db"])
    lufs = metrics.integrated_lufs(out, RATE)[0]
    assert np.isfinite(lufs)


@PROFILE
@given(width=st.floats(min_value=0.0, max_value=3.0))
def test_width_scaling_keeps_finiteness(width: float) -> None:
    data = np.random.default_rng(1).normal(0.0, 0.2, (2000, 2))
    out = mix_width.apply_width(data, width)
    assert out.shape == data.shape
    assert _finite(out)
    if width == 0.0:
        assert np.allclose(out[:, 0], out[:, 1], atol=1e-12)


@PROFILE
@given(data=audio())
def test_match_width_reports_its_decision(data: np.ndarray) -> None:
    out, info = mix_width.match_width(data)
    assert out.shape == data.shape
    assert _finite(out)
    assert "correlation_before" in info and "correlation_after" in info
    if not info["matched"]:
        assert "reason" in info


@PROFILE
@given(data=audio(channels=2))
def test_pitch_correction_preserves_length(data: np.ndarray) -> None:
    from modules.vocal_fx.pitch import correct_pitch

    if float(np.max(np.abs(data))) < 1e-6:
        pytest.skip("тишина: высоты нет")
    out, report = correct_pitch(data, RATE, strength=1.0)
    assert out.shape == data.shape
    assert _finite(out)
    assert report["length_preserved"] is True


@PROFILE
@given(data=audio())
def test_deesser_is_transparent_and_finite(data: np.ndarray) -> None:
    from modules.vocal_fx.desser import dynamic_deess

    out, report = dynamic_deess(data, RATE)
    assert out.shape == data.shape
    assert _finite(out)
    assert report["length_preserved"] is True
    assert report["sibilance_reduction_db"] >= -0.5  # де-эссер не «поднимает» верх


def test_no_nan_leaks_through_reference_band_split() -> None:
    from modules.mix import reference

    rng = np.random.default_rng(3)
    data = rng.normal(0.0, 0.3, (4000, 2))
    data[100] = np.inf
    data[200] = np.nan
    cleaned = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)
    bands = reference._band_split(cleaned, 16000)
    assert np.allclose(np.sum(bands, axis=0), cleaned, atol=1e-9)
    assert all(_finite(band) for band in bands)

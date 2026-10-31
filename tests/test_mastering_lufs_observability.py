"""Regression coverage for optional LUFS measurement diagnostics."""

import types

import numpy as np

from modules import mastering


class _FailingMeter:
    def __init__(self, sample_rate):
        assert sample_rate == 48_000

    def integrated_loudness(self, mono):
        raise RuntimeError("meter input rejected")


def test_lufs_measurement_reports_failed_optional_backend(monkeypatch, caplog):
    samples = np.full((48, 2), 0.1, dtype=np.float64)
    monkeypatch.setattr(mastering, "_HAS_PYLN", True)
    monkeypatch.setattr(mastering, "pyln", types.SimpleNamespace(Meter=_FailingMeter))

    
    level, info = mastering._measure_lufs(samples, 48_000)

    assert level == mastering._loudness_dbfs(samples) - 3.0
    assert info == {
        "lufs_engine": "dbfs_estimate",
        "lufs_status": "failed",
        "lufs_error": "RuntimeError: meter input rejected",
    }
    assert "pyloudnorm measurement failed" in caplog.text


def test_numpy_mastering_returns_explicit_unavailable_lufs_status(monkeypatch):
    samples = np.full((96, 2), 0.05, dtype=np.float64)
    monkeypatch.setattr(mastering, "_HAS_PYLN", False)

    processed, info = mastering._try_numpy_dsp(samples, 48_000, "streaming")

    assert processed.shape == samples.shape
    assert np.isfinite(processed).all()
    assert info["lufs_engine"] == "dbfs_estimate"
    assert info["lufs_status"] == "unavailable"
    assert "lufs_error" not in info

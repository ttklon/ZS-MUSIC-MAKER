"""Regression coverage for observable optional LUFS analysis fallback."""

import types

import numpy as np

from modules.hit_scorer import mix_metrics as hit_scorer


class _FailingMeter:
    def __init__(self, sample_rate):
        assert sample_rate == 22_050

    def integrated_loudness(self, samples):
        raise ValueError("short clip")


def test_lufs_status_reports_failed_optional_meter(monkeypatch, caplog):
    samples = np.full(128, 0.1, dtype=np.float64)
    monkeypatch.setattr(hit_scorer, "HAS_PYLOUDNORM", True)
    monkeypatch.setattr(
        hit_scorer, "pyln", types.SimpleNamespace(Meter=_FailingMeter), raising=False
    )

    result, provenance = hit_scorer._loudness_lufs_status(samples, 22_050)

    assert result == hit_scorer._loudness_rms_estimate(samples)
    assert provenance == {
        "engine": "rms_estimate",
        "status": "failed",
        "error": "ValueError: short clip",
    }
    assert "pyloudnorm analysis failed" in caplog.text
    assert hit_scorer._loudness_lufs(samples, 22_050) == result


def test_lufs_status_labels_missing_optional_meter_as_estimate(monkeypatch):
    samples = np.full(128, 0.1, dtype=np.float64)
    monkeypatch.setattr(hit_scorer, "HAS_PYLOUDNORM", False)

    result, provenance = hit_scorer._loudness_lufs_status(samples, 22_050)

    assert result == hit_scorer._loudness_rms_estimate(samples)
    assert provenance == {"engine": "rms_estimate", "status": "unavailable"}

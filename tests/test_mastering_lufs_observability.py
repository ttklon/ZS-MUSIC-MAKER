"""LUFS-диагностика: честный статус вместо тихой подмены метрики.

Гейты громкости не имеют права притворяться: если измеритель недоступен или
падает, результат помечается `dbfs_estimate` + статус, а не «настоящий LUFS».
"""

from __future__ import annotations

import types

import numpy as np

from modules.dsp import metrics


class _FailingMeter:
    def __init__(self, sample_rate):
        assert sample_rate == 48_000

    def integrated_loudness(self, audio):
        raise RuntimeError("meter input rejected")


def test_lufs_measurement_reports_failed_optional_backend(monkeypatch):
    samples = np.full((48, 2), 0.1, dtype=np.float64)
    fake_pyln = types.SimpleNamespace(Meter=_FailingMeter)
    monkeypatch.setitem(__import__("sys").modules, "pyloudnorm", fake_pyln)

    level, info = metrics.integrated_lufs(samples, 48_000)

    assert info["lufs_engine"] == "dbfs_estimate"
    assert info["lufs_status"] == "failed"
    assert "meter input rejected" in info["lufs_error"]
    assert level == metrics.rms_dbfs(samples) - 3.0


def test_lufs_reports_unavailable_without_pyloudnorm(monkeypatch):
    samples = np.full((96, 2), 0.05, dtype=np.float64)
    import builtins

    real_import = builtins.__import__

    def _no_pyloudnorm(name, *args, **kwargs):
        if name == "pyloudnorm":
            raise ImportError("pyloudnorm is not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_pyloudnorm)

    level, info = metrics.integrated_lufs(samples, 48_000)

    assert info == {"lufs_engine": "dbfs_estimate", "lufs_status": "unavailable"}
    assert level == metrics.rms_dbfs(samples) - 3.0


def test_stereo_lufs_is_three_db_louder_than_mono_downmix():
    """BS.1770 суммирует каналы: моно-даункмикс систематически занижает LUFS."""
    sample_rate = 44_100
    time = np.arange(sample_rate * 3) / sample_rate
    mono = 0.2 * np.sin(2 * np.pi * 440 * time)
    stereo = np.stack([mono, mono], axis=1)

    stereo_lufs, _ = metrics.integrated_lufs(stereo, sample_rate)
    mono_lufs, _ = metrics.integrated_lufs(mono, sample_rate)

    assert 2.5 <= stereo_lufs - mono_lufs <= 3.5

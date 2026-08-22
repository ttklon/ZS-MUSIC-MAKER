"""Regression coverage for observable optional Essentia analysis fallback."""

import builtins

import numpy as np

from modules import analyzer


def test_analyze_audio_reports_failed_optional_essentia(monkeypatch):
    monkeypatch.setattr(analyzer.librosa, "load", lambda path, sr=None, mono=True: (np.ones(4096), 22050))
    monkeypatch.setattr(analyzer.librosa.beat, "beat_track", lambda y, sr: (120.0, np.array([1, 2])))
    monkeypatch.setattr(analyzer.librosa, "yin", lambda y, fmin, fmax, sr: np.array([440.0]))
    monkeypatch.setattr(analyzer.librosa.feature, "chroma_cqt", lambda y, sr: np.ones((12, 2)))
    monkeypatch.setattr(analyzer.librosa.feature, "spectral_centroid", lambda y, sr: np.array([[1000.0]]))
    monkeypatch.setattr(analyzer.librosa.feature, "spectral_bandwidth", lambda y, sr: np.array([[500.0]]))
    monkeypatch.setattr(analyzer.librosa.feature, "zero_crossing_rate", lambda y: np.array([[0.1]]))
    monkeypatch.setattr(analyzer.librosa.feature, "rms", lambda y, frame_length=None, hop_length=None: np.array([[0.2] * 8]))
    real_import = builtins.__import__

    def blocked_essentia(name, *args, **kwargs):
        if name.startswith("essentia"):
            raise ModuleNotFoundError("No module named 'essentia'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_essentia)

    result = analyzer.analyze_single("fake.wav")

    assert result["essentia"] == {}
    assert result["essentia_status"] == {
        "ok": False,
        "status": "failed",
        "error": "ModuleNotFoundError: No module named 'essentia'",
    }

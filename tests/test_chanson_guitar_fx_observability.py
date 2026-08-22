"""Regression coverage for observable optional Chanson guitar-effects fallback."""

import numpy as np

from modules import chanson_engine


def test_guitar_effects_label_unavailable_pedalboard(monkeypatch):
    engine = chanson_engine.ChansonEngine(sample_rate=8_000)
    dry = np.array([0.1, -0.1], dtype=np.float32)
    monkeypatch.setattr(chanson_engine, "HAS_PEDALBOARD", False)

    result, status = engine._apply_guitar_effects(dry)

    assert result is dry
    assert status == {
        "ok": False,
        "engine": "numpy_guitar",
        "status": "unavailable",
    }


def test_guitar_effects_report_failed_pedalboard_and_retain_dry_signal(monkeypatch, caplog):
    engine = chanson_engine.ChansonEngine(sample_rate=8_000)
    dry = np.array([0.1, -0.1], dtype=np.float32)

    class _FailingBoard:
        def __init__(self, effects):
            raise RuntimeError("effect plugin load failed")

    monkeypatch.setattr(chanson_engine, "HAS_PEDALBOARD", True)
    monkeypatch.setattr(chanson_engine, "Pedalboard", _FailingBoard, raising=False)
    monkeypatch.setattr(chanson_engine, "Chorus", lambda **kwargs: kwargs, raising=False)
    monkeypatch.setattr(chanson_engine, "Reverb", lambda **kwargs: kwargs, raising=False)

    result, status = engine._apply_guitar_effects(dry)

    assert result is dry
    assert status == {
        "ok": False,
        "engine": "numpy_guitar",
        "status": "failed",
        "error": "RuntimeError: effect plugin load failed",
    }
    assert "retaining dry synthesis" in caplog.text

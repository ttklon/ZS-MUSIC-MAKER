"""Regression coverage for observable optional Chanson master-bus fallback."""

import numpy as np

from modules import chanson_engine


def test_master_bus_labels_unavailable_pedalboard(monkeypatch):
    engine = chanson_engine.ChansonEngine(sample_rate=8_000)
    mix = np.ones((16, 2), dtype=np.float32) * 0.1
    monkeypatch.setattr(chanson_engine, "HAS_PEDALBOARD", False)

    result, status = engine._apply_master_bus(mix)

    assert result is mix
    assert status == {
        "ok": False,
        "engine": "numpy_raw_mix",
        "status": "unavailable",
    }


def test_master_bus_reports_failed_pedalboard_and_retains_mix(monkeypatch, caplog):
    engine = chanson_engine.ChansonEngine(sample_rate=8_000)
    mix = np.ones((16, 2), dtype=np.float32) * 0.1

    class _FailingBoard:
        def __init__(self, effects):
            raise RuntimeError("plugin load failed")

    monkeypatch.setattr(chanson_engine, "HAS_PEDALBOARD", True)
    monkeypatch.setattr(chanson_engine, "Pedalboard", _FailingBoard, raising=False)
    monkeypatch.setattr(chanson_engine, "HighpassFilter", lambda **kwargs: kwargs, raising=False)
    monkeypatch.setattr(chanson_engine, "Compressor", lambda **kwargs: kwargs, raising=False)
    monkeypatch.setattr(chanson_engine, "Limiter", lambda **kwargs: kwargs, raising=False)

    result, status = engine._apply_master_bus(mix)

    assert result is mix
    assert status == {
        "ok": False,
        "engine": "numpy_raw_mix",
        "status": "failed",
        "error": "RuntimeError: plugin load failed",
    }
    assert "retaining raw mix" in caplog.text

"""Regression coverage for CyberSynth optional Pedalboard fallback provenance."""

import numpy as np

from modules import cyber_synth


def test_cyber_master_bus_marks_unavailable_pedalboard(monkeypatch):
    synth = cyber_synth.CyberSynth(sample_rate=8_000)
    mix = np.zeros((4, 2), dtype=np.float32)
    monkeypatch.setattr(cyber_synth, "HAS_PEDALBOARD", False)

    result, status = synth._apply_master_bus(mix)

    assert result is mix
    assert status == {"ok": False, "engine": "numpy_raw_mix", "status": "unavailable"}

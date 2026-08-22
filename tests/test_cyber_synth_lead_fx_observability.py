"""Regression coverage for CyberSynth optional lead-effects fallback."""

import numpy as np

from modules import cyber_synth


def test_cyber_lead_effects_mark_unavailable_pedalboard(monkeypatch):
    synth = cyber_synth.CyberSynth(sample_rate=8_000)
    lead = np.array([0.1, -0.1], dtype=np.float32)
    monkeypatch.setattr(cyber_synth, "HAS_PEDALBOARD", False)

    result, status = synth._apply_lead_effects(lead)

    assert result is lead
    assert status == {"ok": False, "engine": "numpy_fm_lead", "status": "unavailable"}

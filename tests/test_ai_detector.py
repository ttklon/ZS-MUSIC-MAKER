from __future__ import annotations

import numpy as np
import soundfile as sf

from modules.ai_detector_pro import analyze_track


def test_ai_detector_reports_explicit_internal_risk_metric(tmp_path) -> None:
    sample_rate = 8_000
    seconds = 4
    time_axis = np.arange(sample_rate * seconds) / sample_rate
    audio = 0.1 * np.sin(2 * np.pi * 220 * time_axis)
    path = tmp_path / "synthetic.wav"
    sf.write(path, audio, sample_rate)

    report = analyze_track(str(path))

    assert report["ok"] is True
    assert 0.0 <= report["ai_risk_percent"] <= 100.0
    assert report["metric_type"] == "internal_audio_heuristic_not_ai_attribution"
    assert "vocal_liveliness" in report["metrics"]

from __future__ import annotations

import numpy as np
import soundfile as sf

from modules.phonk_engine import generate_cowbell


def test_generate_cowbell_returns_in_memory_waveform_for_v2_contract() -> None:
    waveform = generate_cowbell(440.0, duration_sec=0.3, sample_rate=8_000)

    assert isinstance(waveform, np.ndarray)
    assert waveform.dtype == np.float32
    assert len(waveform) == 2_400
    assert float(np.max(np.abs(waveform))) > 0.01


def test_generate_cowbell_preserves_legacy_file_output(tmp_path) -> None:
    target = tmp_path / "cowbell.wav"
    result = generate_cowbell([440.0, 660.0], bpm=140, out_path=str(target), sample_rate=8_000)

    audio, sample_rate = sf.read(result)
    assert str(target) == result
    assert sample_rate == 8_000
    assert len(audio) == 1_600

"""
Mastering results validation (F1, F4)
====================================
Verifies that the mastering engine produces valid, high-quality audio.
"""

import sys
from pathlib import Path
import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modules.pro_audio_dsp import ProAudioDSP  # pylint: disable=wrong-import-position
from tests.test_audio_quality import (  # pylint: disable=wrong-import-position
    validate_audio_file,
)


def test_pro_mastering_quality_output(tmp_path: Path) -> None:
    """Verifies that ProAudioDSP produces non-clipping, normalized audio."""
    sr = 44100
    duration = 3.0
    time_vec = np.linspace(0, duration, int(sr * duration))
    # Very quiet raw audio to test normalization
    audio = np.sin(2 * np.pi * 100 * time_vec) * 0.05 + 0.01

    in_file = tmp_path / "raw.wav"
    out_file = tmp_path / "mastered.wav"
    sf.write(str(in_file), audio, sr)

    res = ProAudioDSP.apply_mastering_chain(
        str(in_file), str(out_file), target_lufs=-7.0
    )
    assert res["ok"] is True

    # Validate the mastered file
    validate_audio_file(str(out_file), expected_duration=duration)

    # Verify normalization (should be loud)
    data, _ = sf.read(str(out_file))
    peak = np.max(np.abs(data))
    assert peak > 0.6, f"Mastering failed to normalize adequately. Peak: {peak}"
    assert peak <= 1.0, "Mastering caused clipping!"

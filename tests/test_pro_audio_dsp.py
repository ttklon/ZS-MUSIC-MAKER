"""
Unit tests for ProAudioDSP adhering to Genspark / Claude Code rigorous standards.
"""

from pathlib import Path
import sys
import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modules.pro_audio_dsp import ProAudioDSP  # pylint: disable=wrong-import-position


def test_stereo_phase_alignment() -> None:
    """Test stereo phase alignment and delay correction."""
    sr = 22050
    t = np.linspace(0, 1, sr)
    left = np.sin(2 * np.pi * 440 * t)
    right = np.sin(2 * np.pi * 440 * t + 0.1)
    stereo = np.stack([left, right], axis=1)

    aligned = ProAudioDSP.align_stereo_phases(stereo)
    assert aligned.shape == stereo.shape
    assert not np.isnan(aligned).any()


def test_mastering_chain(tmp_path: Path) -> None:
    """Test professional mastering pipeline and output file generation."""
    sr = 22050
    t = np.linspace(0, 2, sr * 2)
    audio = (
        np.stack(
            [np.sin(2 * np.pi * 220 * t), np.cos(2 * np.pi * 220 * t)], axis=1
        )
        * 0.5
    )

    in_file = tmp_path / "test_in.wav"
    out_file = tmp_path / "test_out.wav"
    sf.write(str(in_file), audio, sr)

    res = ProAudioDSP.apply_mastering_chain(
        str(in_file), str(out_file), target_lufs=-14.0
    )
    assert res["ok"] is True
    assert Path(out_file).exists()

    out_data, _ = sf.read(str(out_file))
    assert np.max(np.abs(out_data)) <= 1.0

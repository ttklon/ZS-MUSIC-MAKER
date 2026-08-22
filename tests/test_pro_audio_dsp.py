"""
Unit tests for ProAudioDSP adhering to Genspark / Claude Code rigorous standards.
"""

from pathlib import Path
import sys
import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modules.pro_audio_dsp import ProAudioDSP  # pylint: disable=wrong-import-position
from tools.audio_golden_metrics import audio_signature  # pylint: disable=wrong-import-position
from tools.generate_audio_goldens import golden_vocal_signal  # pylint: disable=wrong-import-position

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "audio"


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


def test_golden_vocal_fixture_signature_is_stable() -> None:
    signature = audio_signature(FIXTURE_DIR / "golden_vocal_10s.wav")

    assert signature["sample_rate"] == 44_100
    assert signature["channels"] == 1
    assert signature["duration_sec"] == 10.0
    assert 0.15 <= signature["peak"] <= 0.18
    assert 0.058 <= signature["rms"] <= 0.066
    assert 800 <= signature["spectral_centroid_hz"] <= 890


def test_deterministic_vocal_rerender_matches_golden_features(tmp_path: Path) -> None:
    rerender_path = tmp_path / "vocal.wav"
    sf.write(rerender_path, golden_vocal_signal(), 44_100, subtype="PCM_24")

    golden = audio_signature(FIXTURE_DIR / "golden_vocal_10s.wav")
    rerender = audio_signature(rerender_path)

    assert rerender["duration_sec"] == golden["duration_sec"]
    assert abs(rerender["rms"] - golden["rms"]) / golden["rms"] <= 0.05
    assert abs(rerender["peak"] - golden["peak"]) <= 0.01
    assert abs(rerender["spectral_centroid_hz"] - golden["spectral_centroid_hz"]) / golden["spectral_centroid_hz"] <= 0.05


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

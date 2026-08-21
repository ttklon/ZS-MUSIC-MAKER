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
from tools.audio_golden_metrics import audio_signature  # pylint: disable=wrong-import-position

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "audio"


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


def _golden_master_input(sample_rate: int = 44_100, duration_sec: int = 10) -> np.ndarray:
    time = np.arange(sample_rate * duration_sec, dtype=np.float64) / sample_rate
    raw = (
        0.045 * np.sin(2 * np.pi * 92 * time)
        + 0.020 * np.sin(2 * np.pi * 220 * time)
        + 0.006 * np.sin(2 * np.pi * 1740 * time)
    )
    return np.column_stack((raw, raw * 0.96 + 0.001 * np.sin(2 * np.pi * 0.7 * time)))


def test_golden_master_fixture_signature_is_stable() -> None:
    """The committed master fixture documents a reproducible DSP baseline."""
    signature = audio_signature(FIXTURE_DIR / "golden_master_10s.wav")

    assert signature["sample_rate"] == 44_100
    assert signature["channels"] == 2
    assert signature["duration_sec"] == 10.0
    assert 0.70 <= signature["peak"] <= 0.75
    assert 0.34 <= signature["rms"] <= 0.37
    assert 250 <= signature["spectral_centroid_hz"] <= 340


def test_deterministic_master_rerender_matches_golden_features(tmp_path: Path) -> None:
    """Reject material drift in the available local mastering DSP chain."""
    raw_path = tmp_path / "golden_raw.wav"
    rerender_path = tmp_path / "golden_master.wav"
    sf.write(raw_path, _golden_master_input(), 44_100, subtype="PCM_24")

    result = ProAudioDSP.apply_mastering_chain(
        str(raw_path), str(rerender_path), target_lufs=-9.0
    )
    assert result["ok"] is True

    golden = audio_signature(FIXTURE_DIR / "golden_master_10s.wav")
    rerender = audio_signature(rerender_path)
    assert rerender["duration_sec"] == golden["duration_sec"]
    assert abs(rerender["rms"] - golden["rms"]) / golden["rms"] <= 0.05
    assert abs(rerender["peak"] - golden["peak"]) <= 0.03
    assert abs(rerender["spectral_centroid_hz"] - golden["spectral_centroid_hz"]) / golden["spectral_centroid_hz"] <= 0.05

"""
Professional Audio Quality Validation Suite (Category F)
=======================================================
Verifies peak levels, clipping, duration, and signal presence.
"""

import os
from pathlib import Path
from typing import Optional
import numpy as np
import soundfile as sf


def validate_audio_file(
    path: str, expected_duration: Optional[float] = None, tolerance: float = 0.5
) -> None:
    """
    Core validator for audio artifacts.
    Checks:
    1. File existence and readability.
    2. No digital clipping (peaks <= 1.0).
    3. Signal presence (RMS > 0).
    4. Duration accuracy.
    """
    assert os.path.exists(path), f"File not found: {path}"
    data, sr = sf.read(path)

    # 1. Check for clipping (with float precision awareness)
    peak = np.max(np.abs(data))
    assert peak <= 1.0001, f"Audio is clipping! Peak: {peak}"

    # 2. Check for silence
    rms = np.sqrt(np.mean(data**2))
    assert rms > 1e-4, f"Audio is too quiet or silent. RMS: {rms}"

    # 3. Check duration
    if expected_duration:
        actual_duration = len(data) / sr
        assert abs(actual_duration - expected_duration) <= tolerance, (
            f"Duration mismatch: {actual_duration}s != {expected_duration}s"
        )


def test_placeholder_audio_quality(tmp_path: Path) -> None:
    """Verifies the validator itself with a generated sine wave."""
    sr = 22050
    duration = 2.0
    time_vec = np.linspace(0, duration, int(sr * duration))
    # Safe sine wave (no clipping)
    audio = np.sin(2 * np.pi * 440 * time_vec) * 0.8

    path = tmp_path / "test.wav"
    sf.write(str(path), audio, sr)

    validate_audio_file(str(path), expected_duration=duration)


def test_clipping_detection(tmp_path: Path) -> None:
    """Verifies that the validator correctly identifies clipping."""
    import pytest  # pylint: disable=import-outside-toplevel

    sr = 22050
    # Create a signal that is clearly clipping
    audio = np.array([1.5, -1.5, 0.0], dtype=np.float32)
    path = tmp_path / "clipped.wav"
    # Write as float to preserve clipping info for the test
    sf.write(str(path), audio, sr, subtype="FLOAT")

    with pytest.raises(AssertionError, match="Audio is clipping"):
        validate_audio_file(str(path))

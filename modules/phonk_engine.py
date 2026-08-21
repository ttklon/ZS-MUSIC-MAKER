"""Canonical Phonk primitives with backward-compatible v1 file-output adapter."""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np


def generate_cowbell(frequency: float | Sequence[float], bpm: int | None = None,
                     out_path: str | None = None, *, duration_sec: float = 0.2,
                     sample_rate: int = 44100):
    """Сгенерировать cowbell waveform либо legacy WAV file.

    Modern consumers (``PhonkEngineV2``) передают frequency и `duration_sec`
    и получают ndarray. Legacy callers с `out_path` получают WAV path.
    """
    if duration_sec <= 0:
        raise ValueError("duration_sec must be positive")
    if isinstance(frequency, Sequence) and not isinstance(frequency, (str, bytes)):
        frequency = float(frequency[0]) if frequency else 800.0
    frequency = float(frequency)
    time_axis = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    envelope = np.exp(-time_axis * 16.0)
    waveform = (
        np.sin(2 * np.pi * frequency * time_axis)
        + 0.35 * np.sin(2 * np.pi * frequency * 2.71 * time_axis)
    ) * envelope * 0.45
    waveform = waveform.astype(np.float32)
    if out_path is None:
        return waveform
    import soundfile as sf

    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    sf.write(target, waveform, sample_rate)
    return str(target)

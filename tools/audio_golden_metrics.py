"""Stable metric helpers for versioned audio golden fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf


def audio_signature(path: str | Path) -> dict[str, float | int]:
    """Return coarse, codec-tolerant audio characteristics for DSP regressions."""
    data, sample_rate = sf.read(path, always_2d=True, dtype="float64")
    mono = data.mean(axis=1)
    window = np.hanning(len(mono))
    spectrum = np.abs(np.fft.rfft(mono * window))
    freqs = np.fft.rfftfreq(len(mono), d=1.0 / sample_rate)
    spectral_centroid = float(np.sum(freqs * spectrum) / max(np.sum(spectrum), 1e-12))
    correlation = float(np.corrcoef(data[:, 0], data[:, 1])[0, 1]) if data.shape[1] == 2 else 1.0
    return {
        "sample_rate": int(sample_rate),
        "channels": int(data.shape[1]),
        "frames": int(data.shape[0]),
        "duration_sec": float(data.shape[0] / sample_rate),
        "rms": float(np.sqrt(np.mean(np.square(data)))),
        "peak": float(np.max(np.abs(data))),
        "stereo_correlation": correlation,
        "spectral_centroid_hz": spectral_centroid,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Print stable audio golden signature")
    parser.add_argument("path")
    args = parser.parse_args()
    print(json.dumps(audio_signature(args.path), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

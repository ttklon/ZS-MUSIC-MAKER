"""Bounded validation of an explicitly supplied vocal recording."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def inspect_user_vocal(path: str) -> dict[str, Any]:
    """Inspect the complete file in blocks without changing the source."""
    import numpy as np
    import soundfile as sf

    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"recording not found: {source}")
    peak, clipped, samples = 0.0, 0, 0
    with sf.SoundFile(str(source)) as audio:
        duration = len(audio) / audio.samplerate if audio.samplerate else 0.0
        if audio.channels not in (1, 2) or not 8000 <= audio.samplerate <= 192000 or not 0 < duration <= 600:
            raise ValueError("vocal must be mono/stereo, 8–192 kHz and no longer than 600 seconds")
        for block in audio.blocks(blocksize=65536, dtype="float32", always_2d=True):
            if not np.isfinite(block).all():
                raise ValueError("recording contains non-finite samples")
            peak = max(peak, float(np.max(np.abs(block))))
            clipped += int(np.count_nonzero(np.abs(block) >= 0.98))
            samples += int(block.size)
        if not samples or peak < 1e-5:
            raise ValueError("recording is silent")
        return {"duration_sec": round(duration, 3), "sample_rate": audio.samplerate,
                "channels": audio.channels, "peak": peak,
                "near_clip_samples": clipped, "near_clip_fraction": round(clipped / samples, 6),
                "near_clipping_warning": clipped > 0}

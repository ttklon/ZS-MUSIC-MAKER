"""Safely bring a user-selected instrumental into a project as WAV."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


def import_instrumental(source: str, destination: Path) -> dict:
    """Copy in chunks; never mutate the source or use an invalid/silent file."""
    import numpy as np
    import soundfile as sf

    src = Path(source)
    if not src.is_file():
        raise FileNotFoundError(f"instrumental file not found: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with sf.SoundFile(str(src)) as audio:
            duration = len(audio) / audio.samplerate if audio.samplerate else 0
            if audio.channels not in (1, 2) or audio.samplerate < 8000 or not 0.25 <= duration <= 600:
                raise ValueError("instrumental must be mono/stereo, 8kHz+ and 0.25–600 seconds")
            fd, name = tempfile.mkstemp(dir=destination.parent, suffix=".wav")
            os.close(fd)
            temp_path = Path(name)
            peak = 0.0
            with sf.SoundFile(str(temp_path), mode="w", samplerate=audio.samplerate,
                              channels=audio.channels, format="WAV", subtype="PCM_24") as output:
                for block in audio.blocks(blocksize=65536, dtype="float32", always_2d=True):
                    if not np.isfinite(block).all():
                        raise ValueError("instrumental contains non-finite samples")
                    peak = max(peak, float(np.max(np.abs(block))))
                    if peak > 1.0001:
                        raise ValueError("instrumental contains clipped samples")
                    output.write(block)
            if peak < 1e-5:
                raise ValueError("instrumental is silent")
        os.replace(temp_path, destination)
        return {"ok": True, "path": str(destination), "engine": "user_instrumental",
                "duration_sec": round(duration, 2), "source": str(src)}
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

"""Bounded real audio validation; metadata and a path alone cannot prove a render."""
from __future__ import annotations

import hashlib
from pathlib import Path


def inspect_audio(filename: str | None, max_seconds: float = 1800) -> dict:
    result = {"valid": False, "path": filename, "reason": "нет аудиофайла"}
    if not filename:
        return result
    try:
        import numpy as np
        import soundfile as sf

        path = Path(filename)
        with sf.SoundFile(path) as audio:
            seconds = len(audio) / audio.samplerate
            if seconds < 0.1 or seconds > max_seconds or audio.channels not in (1, 2):
                raise ValueError("недопустимая длительность или число каналов")
            peak = 0.0
            for block in audio.blocks(blocksize=65536, dtype="float32", always_2d=True):
                if not np.isfinite(block).all():
                    raise ValueError("аудио содержит NaN/Inf")
                peak = max(peak, float(np.abs(block).max(initial=0)))
            if peak < 0.00001 or peak > 1.001:
                raise ValueError("тишина или превышение цифрового диапазона")
            result.update(seconds=seconds, sample_rate=audio.samplerate, channels=audio.channels, peak=peak)
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        result.update(valid=True, sha256=digest.hexdigest(), bytes=path.stat().st_size, reason="")
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
    return result

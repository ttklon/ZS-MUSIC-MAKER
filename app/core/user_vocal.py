"""Bounded validation of an explicitly supplied vocal recording."""
from __future__ import annotations

from pathlib import Path
import re
import shutil
import tempfile
from typing import Any


def prepare_user_vocal(path: str, expected_sha256: str, out_root: Path) -> tuple[str, dict[str, Any]]:
    """Use a verified private copy when a recording fingerprint is available.

    Detects ordinary changes, not hostile concurrent file replacement. Old takes
    without a fingerprint remain usable, but cannot be verified retrospectively.
    """
    if not expected_sha256:
        return path, inspect_user_vocal(path)
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ValueError("invalid recording SHA-256")
    from app.core.input_integrity import _file_info

    source = Path(path)
    original = _file_info(source)
    if original[1] != expected_sha256:
        raise ValueError("recording does not match its saved SHA-256")
    out_root.mkdir(parents=True, exist_ok=True)
    suffix = source.suffix.lower()
    if not re.fullmatch(r"\.[a-z0-9]{1,12}", suffix):
        suffix = ".bin"
    target = None
    try:
        with tempfile.NamedTemporaryFile(prefix="vocal-source-", suffix=suffix, dir=out_root, delete=False) as file:
            target = Path(file.name)
            with source.open("rb") as src:
                shutil.copyfileobj(src, file)
        if _file_info(target) != original or _file_info(source) != original:
            raise ValueError("recording changed or vocal copy failed integrity check")
        return str(target), inspect_user_vocal(str(target))
    except BaseException:
        if target is not None:
            target.unlink(missing_ok=True)
        raise


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

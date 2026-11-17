"""Validate and atomically publish vocal renders; never reuse a stale WAV."""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import numpy as np

_LOG = logging.getLogger(__name__)


def read_voice(path: str):
    """A large file is not evidence of sound: decode and verify actual samples."""
    import soundfile as sf

    audio, sr = sf.read(path, dtype="float32", always_2d=True)
    if (sr <= 0 or not audio.size or audio.shape[1] not in (1, 2)
            or not np.isfinite(audio).all() or not np.any(audio)):
        raise ValueError("voice output is empty, silent, non-finite or has unsupported channels")
    return audio, sr


def usable_voice(path: str) -> bool:
    try:
        read_voice(path)
        return True
    except (OSError, RuntimeError, ValueError):
        return False


def render_atomic(target: str, render) -> bool:
    """Preserve previous good audio on any failure, isolate concurrent projects.

    Each invocation renders to its own sibling temporary directory. Publish
    only verified, canonical WAV, even when a backend actually emitted MP3.
    Temporary files are removed on success, failure and exceptions.
    """
    from modules.dsp.wavio import write_wav

    destination = Path(target)
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".voice-", dir=destination.parent) as tmp:
            staged = Path(tmp) / "voice.wav"
            if not render(str(staged)):
                return False
            audio, sr = read_voice(str(staged))
            write_wav(staged, audio, sr)
            staged.replace(destination)
        return True
    except (OSError, RuntimeError, ValueError) as exc:
        _LOG.warning("vocal render not published: %s", exc)
        return False

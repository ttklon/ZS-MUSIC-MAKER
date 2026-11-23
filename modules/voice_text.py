"""Bounded neural-TTS input and deterministic assembly of long draft vocals."""
from __future__ import annotations

import re
import textwrap

import numpy as np

_LABEL = re.compile(
    r"^\s*\[(?:(?:verse|куплет)\s*\d*|chorus|hook|припев|intro|outro|bridge|бридж)\]\s*$",
    re.IGNORECASE,
)


def speech_chunks(text: str, max_chars: int = 600) -> list[str]:
    """Strip section labels, retaining lyrics and punctuation in bounded chunks.

    Prefer sentence/line boundaries; very long sentences are split at words.
    No truncation: every non-label word is included in order.
    """
    if max_chars < 32:
        raise ValueError("TTS chunk size must be at least 32 characters")
    lines = [line.strip() for line in text.splitlines() if not _LABEL.fullmatch(line)]
    sentences = re.split(r"(?<=[.!?…;:])\s+|\n+", "\n".join(lines))
    chunks: list[str] = []
    pending = ""
    for sentence in sentences:
        for part in textwrap.wrap(sentence, width=max_chars, break_on_hyphens=False):
            if pending and len(pending) + len(part) + 1 > max_chars:
                chunks.append(pending)
                pending = ""
            pending = f"{pending} {part}".strip()
    if pending:
        chunks.append(pending)
    return chunks


def silero_audio(model, text: str, speaker: str, sample_rate: int = 48000) -> np.ndarray:
    """Load the model once, synthesize all chunks, fail rather than drop a verse."""
    chunks = speech_chunks(text)
    if not chunks:
        raise ValueError("no spoken lyrics after section labels")
    parts: list[np.ndarray] = []
    for chunk in chunks:
        tensor = model.apply_tts(text=chunk, speaker=speaker, sample_rate=sample_rate)
        audio = np.asarray(tensor.detach().cpu().numpy(), dtype=np.float32)
        if audio.ndim != 1 or not audio.size or not np.isfinite(audio).all():
            raise ValueError("Silero returned empty, non-mono or non-finite audio")
        if not np.any(audio):
            raise ValueError("Silero returned silence")
        # Short edge fades prevent clicks when separately rendered phrases meet.
        audio = audio.copy()
        fade = min(round(sample_rate * 0.005), len(audio) // 2)
        if fade:
            ramp = np.linspace(0, 1, fade, dtype=np.float32)
            audio[:fade] *= ramp
            audio[-fade:] *= ramp[::-1]
        if parts:
            parts.append(np.zeros(round(sample_rate * 0.08), dtype=np.float32))
        parts.append(audio)
    return np.concatenate(parts)

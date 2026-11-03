"""Opt-in, local-only reference speech recognition for lyric context.

No automatic download, source separation, transcript file, or accuracy claim.
Audio is decoded only up to a fixed limit and the model is released after use.
"""
from __future__ import annotations

from pathlib import Path
import math
import re
from typing import Any

MAX_REFERENCES = 7
MAX_SECONDS = 180
SAMPLE_RATE = 16000
MAX_TEXT_CHARS = 20000
MAX_SEGMENTS = 1000


def _decode_bounded(path: Path) -> tuple[Any, bool]:
    """Decode mono 16 kHz audio with PyAV; stop after one sample past the limit."""
    import av
    import numpy as np

    limit = SAMPLE_RATE * MAX_SECONDS
    resampler = av.audio.resampler.AudioResampler(format="flt", layout="mono", rate=SAMPLE_RATE)
    parts = []
    samples = 0
    with av.open(str(path), mode="r", metadata_errors="ignore") as container:
        for frame in container.decode(audio=0):
            frame.pts = None
            for converted in resampler.resample(frame):
                data = converted.to_ndarray().reshape(-1)
                take = min(len(data), limit + 1 - samples)
                if take:
                    parts.append(data[:take].copy())
                    samples += take
                if samples > limit:
                    break
            if samples > limit:
                break
        else:
            for converted in resampler.resample(None):
                data = converted.to_ndarray().reshape(-1)
                take = min(len(data), limit + 1 - samples)
                if take:
                    parts.append(data[:take].copy())
                    samples += take
                if samples > limit:
                    break
    audio = np.concatenate(parts)[:limit].astype(np.float32, copy=False) if parts else np.empty(0, dtype=np.float32)
    if not audio.size or not np.isfinite(audio).all():
        raise ValueError("audio is empty or contains invalid samples")
    return audio, samples > limit


def _transcribe_one(model: Any, path: Path, index: int) -> tuple[str, dict[str, Any]]:
    from app.ai.quality import validate_asr_transcript

    row: dict[str, Any] = {"index": index, "file": path.name}
    try:
        if not path.is_file():
            raise FileNotFoundError("reference audio not found")
        audio, audio_truncated = _decode_bounded(path)
        segments, info = model.transcribe(audio, language=None, beam_size=5, vad_filter=True,
                                          condition_on_previous_text=False)
        lines: list[str] = []
        length = 0
        output_truncated = False
        for number, segment in enumerate(segments):
            if number >= MAX_SEGMENTS:
                output_truncated = True
                break
            line = str(getattr(segment, "text", "") or "").strip()
            if not line:
                continue
            remaining = MAX_TEXT_CHARS - length
            if len(line) > remaining:
                line = line[:remaining]
                output_truncated = True
            if line:
                lines.append(line)
                length += len(line) + 1
            if output_truncated or length >= MAX_TEXT_CHARS:
                output_truncated = True
                break
        text = "\n".join(lines).strip()
        quality = validate_asr_transcript(text)
        language = str(getattr(info, "language", "") or "")
        language = language if re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z]{2,4})?", language) else ""
        try:
            probability = float(getattr(info, "language_probability", None))
            if not math.isfinite(probability) or not 0 <= probability <= 1:
                probability = None
        except (TypeError, ValueError):
            probability = None
        row.update(status="INFERRED_UNVERIFIED" if quality["ok"] else "NO_USABLE_TEXT",
                   language=language, language_probability=probability,
                   audio_seconds=round(len(audio) / SAMPLE_RATE, 2),
                   audio_truncated=audio_truncated, output_truncated=output_truncated,
                   quality=quality)
        return (text if quality["ok"] else ""), row
    except Exception as exc:  # noqa: BLE001 - retain per-reference diagnostics
        # Backend exceptions can contain decoded content. Do not persist their message.
        row.update(status="FAILED", reason="audio decode or ASR failed", error_type=type(exc).__name__)
        return "", row


def transcribe_references(paths: list[str], *, model_registry: Any = None) -> tuple[str, dict[str, Any]]:
    """Run local ASR once per selected reference and return only in-memory text."""
    report: dict[str, Any] = {
        "requested": True, "status": "BLOCKED", "engine": None, "items": [],
        "max_references": MAX_REFERENCES, "max_seconds_per_reference": MAX_SECONDS,
        "source_separation": False, "transcript_saved": False,
        "accuracy_verified": False, "reason": None,
    }
    if not paths:
        report["reason"] = "no reference audio supplied"
        return "", report
    if model_registry is None:
        from app.ai.registry import registry
        model_registry = registry
    try:
        available = model_registry.is_available("asr")
    except Exception as exc:  # noqa: BLE001 - report the failed availability check
        report["reason"] = f"ASR availability check failed: {type(exc).__name__}: {exc}"
        return "", report
    if not available:
        report["reason"] = "local faster-whisper package or model weights unavailable"
        return "", report
    texts: list[str] = []
    try:
        with model_registry.use("asr", unload_after=True) as loaded:
            report["engine"] = loaded.engine
            report["device"] = loaded.device
            for index, source in enumerate(paths[:MAX_REFERENCES], 1):
                text, row = _transcribe_one(loaded.handle, Path(source), index)
                report["items"].append(row)
                if text:
                    texts.append(text)
    except Exception as exc:  # noqa: BLE001 - model load/preflight failure is not successful inference
        message = str(exc)
        if isinstance(exc, RuntimeError) and message.startswith("Insufficient or unknown free RAM for ASR:"):
            report["reason"] = message
        else:
            report["reason"] = f"ASR model unavailable: {type(exc).__name__}"
        return "", report
    for index, source in enumerate(paths[MAX_REFERENCES:], MAX_REFERENCES + 1):
        report["items"].append({"index": index, "file": Path(source).name,
                                "status": "SKIPPED", "reason": "reference limit"})
    if not texts:
        report["status"] = "NO_USABLE_TEXT"
        report["reason"] = "no reference produced usable speech text"
        return "", report
    combined = "\n".join(texts)
    limited = len(combined) > MAX_TEXT_CHARS
    report["combined_text_truncated"] = limited
    partial = limited or any(item.get("status") != "INFERRED_UNVERIFIED" or item.get("audio_truncated")
                             or item.get("output_truncated") for item in report["items"])
    report["status"] = "PARTIAL" if partial else "INFERRED_UNVERIFIED"
    return combined[:MAX_TEXT_CHARS], report

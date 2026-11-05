# -*- coding: utf-8 -*-
"""
modules/artist_dossier/features.py — извлечение и ранжирование признаков.

Всё, что можно посчитать по одному аудиофайлу без LLM: Demucs-индекс вокала,
DSP-фичи (BPM/key/длительность/RMS), ранжирование CLAP-тегов и ASR-транскрипт
референса с валидацией качества.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.ai.quality import validate_asr_transcript

def resolve_vocal_source_index(model: Any) -> int:
    """Вернуть индекс stem ``vocals`` из порядка источников фактической Demucs-модели."""
    sources = tuple(getattr(model, "sources", ()) or ())
    if "vocals" not in sources:
        raise ValueError("Demucs model does not expose a 'vocals' source")
    return sources.index("vocals")


def extract_dsp_features(audio_path: str, engine: str = "librosa_dsp") -> dict:
    """Извлечь BPM, key, длительность и RMS через зарегистрированный DSP-движок."""
    try:
        import librosa
        import numpy as np

        y, sr = librosa.load(audio_path, sr=22050, mono=True, duration=180)
        if len(y) == 0:
            return {"ok": False, "reason": "DSP input audio is empty"}
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
        keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        return {
            "ok": True,
            "engine": engine,
            "bpm": float(np.asarray(tempo).reshape(-1)[0]),
            "key": keys[int(np.argmax(chroma))],
            "duration_sec": float(len(y) / sr),
            "loudness_rms": float(np.sqrt(np.mean(y ** 2)) + 1e-9),
        }
    except Exception as exc:
        return {"ok": False, "reason": f"DSP feature extraction failed: {exc}"}


def rank_clap_tags(candidates: list[str], logits: Any, limit: int = 6) -> list[str]:
    """Отсортировать CLAP logits и вернуть уникальные top-N labels из переданного словаря."""
    import numpy as np

    scores = np.asarray(logits).reshape(-1)
    if len(scores) != len(candidates):
        raise ValueError("CLAP scores do not match the candidate vocabulary")
    return [candidates[index] for index in np.argsort(-scores)[:max(1, limit)]]


def transcribe_reference_audio(model: Any, audio_path: str, output_path: str) -> dict:
    """Распознать reference-аудио совместимым faster-whisper handle и сохранить transcript."""
    try:
        segments, info = model.transcribe(audio_path, language="ru", beam_size=5)
        text = "\n".join(
            str(getattr(segment, "text", "")).strip() for segment in segments
        ).strip()
        quality = validate_asr_transcript(text)
        if not quality["ok"]:
            return {
                "ok": False,
                "reason": quality["reason"],
                "quality": quality,
                "fallback": "reference audio retained; transcript is not used",
            }
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return {
            "ok": True,
            "lyrics": text,
            "language": str(getattr(info, "language", "")),
            "source": "faster_whisper",
            "transcript_path": str(target),
            "quality": quality,
            "reason": None,
        }
    except Exception as exc:
        return {"ok": False, "reason": f"ASR transcription failed: {exc}"}

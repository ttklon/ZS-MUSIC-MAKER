# -*- coding: utf-8 -*-
"""
app/ai/quality/analysis.py — проверки результатов анализа: DSP-фичи, CLAP-теги,
ASR-транскрипт, стемы, стерео-текстура, досье трека и артиста.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.ai.quality.audio import audio_metrics, validate_audio_artifact
from app.ai.quality.lyrics import TOKEN_RE


def validate_dsp_features(features: Any) -> dict[str, Any]:
    """Проверить пригодность DSP metadata до использования в dossier/LLM."""
    payload = features if isinstance(features, dict) else {}
    allowed_keys = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"}
    try:
        bpm = float(payload.get("bpm"))
        duration = float(payload.get("duration_sec"))
        rms = float(payload.get("loudness_rms"))
    except (TypeError, ValueError):
        return {"ok": False, "reason": "DSP features are incomplete", "metrics": {"keys": len(payload)}}
    metrics = {"bpm": bpm, "duration_sec": duration, "loudness_rms": rms, "key": payload.get("key")}
    if not 40.0 <= bpm <= 240.0:
        return {"ok": False, "reason": "DSP BPM is outside musical range", "metrics": metrics}
    if payload.get("key") not in allowed_keys:
        return {"ok": False, "reason": "DSP key is invalid", "metrics": metrics}
    if duration <= 0 or rms < 1e-5:
        return {"ok": False, "reason": "DSP audio metrics are invalid", "metrics": metrics}
    return {"ok": True, "reason": None, "metrics": metrics}


def validate_audio_tags(tags: Any, candidates: list[str], *, max_tags: int = 6) -> dict[str, Any]:
    """Проверить CLAP tags: непустой уникальный subset исходного словаря кандидатов."""
    values = list(tags) if isinstance(tags, (list, tuple)) else []
    metrics = {
        "count": len(values),
        "unique_count": len(set(values)),
        "unknown_count": len([tag for tag in values if tag not in candidates]),
    }
    if not values:
        return {"ok": False, "reason": "audio tag output is empty", "metrics": metrics}
    if len(values) > max_tags:
        return {"ok": False, "reason": "audio tag output exceeds limit", "metrics": metrics}
    if metrics["unique_count"] != len(values):
        return {"ok": False, "reason": "audio tag output contains duplicates", "metrics": metrics}
    if metrics["unknown_count"]:
        return {"ok": False, "reason": "audio tag output contains unknown labels", "metrics": metrics}
    return {"ok": True, "reason": None, "metrics": metrics}


def validate_asr_transcript(text: str) -> dict[str, Any]:
    """Проверить пригодность transcript, полученного ASR: содержательность и отсутствие зацикливания."""
    normalized = " ".join((text or "").split())
    tokens = TOKEN_RE.findall(normalized.lower())
    unique_tokens = len(set(tokens))
    metrics = {
        "characters": len(normalized),
        "tokens": len(tokens),
        "unique_tokens": unique_tokens,
        "unique_ratio": round(unique_tokens / len(tokens), 3) if tokens else 0.0,
    }
    if len(normalized) < 3 or not tokens:
        return {"ok": False, "reason": "ASR transcript is empty or too short", "metrics": metrics}
    if len(tokens) >= 4 and metrics["unique_ratio"] <= 0.25:
        return {"ok": False, "reason": "ASR transcript is excessively repetitive", "metrics": metrics}
    return {"ok": True, "reason": None, "metrics": metrics}


def validate_stem_artifact(input_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    """Проверить stem Demucs: пригодный audio output с длительностью исходного трека."""
    source = audio_metrics(input_path)
    if not source.get("readable"):
        return {"ok": False, "reason": "stem input audio is unreadable", "metrics": {"input": source}}
    result = validate_audio_artifact(output_path, min_duration_sec=0.25)
    result["metrics"]["input_duration_sec"] = source.get("duration_sec")
    if not result["ok"]:
        return result
    input_duration = float(source["duration_sec"])
    ratio = float(result["metrics"]["duration_sec"]) / input_duration if input_duration > 0 else 0.0
    result["metrics"]["duration_ratio"] = round(ratio, 3)
    if not 0.95 <= ratio <= 1.05:
        return {"ok": False, "reason": "stem duration diverges from input", "metrics": result["metrics"]}
    return {"ok": True, "reason": None, "metrics": result["metrics"]}


def validate_stereo_texture(path: str | Path, *, min_duration_sec: float = 1.0) -> dict[str, Any]:
    """Проверить, что texture-artifact является слышимым и фактически стерео."""
    base = validate_audio_artifact(path, min_duration_sec=min_duration_sec)
    if not base["ok"]:
        return base
    metrics = base["metrics"]
    if metrics.get("channels") != 2:
        return {"ok": False, "reason": "texture is not stereo", "metrics": metrics}
    if metrics.get("stereo_side_rms", 0.0) < 5e-4:
        return {"ok": False, "reason": "stereo side energy too low", "metrics": metrics}
    if abs(metrics.get("stereo_correlation", 1.0)) > 0.995:
        return {"ok": False, "reason": "stereo channels are over-correlated", "metrics": metrics}
    return {"ok": True, "reason": None, "metrics": metrics}


def validate_analysis_json(payload: Any, *, track_level: bool = False) -> dict[str, Any]:
    """Проверить минимальный контракт JSON-ответа analysis_llm."""
    if not isinstance(payload, dict):
        return {"ok": False, "reason": "analysis response is not an object", "metrics": {}}

    required = ("theme", "storyline", "key_lines", "analysis", "hook", "reusable_elements") if track_level else (
        "bio",
        "themes",
        "slang",
        "flow",
        "analogs",
    )
    missing = [key for key in required if not payload.get(key)]
    if missing:
        return {
            "ok": False,
            "reason": "missing analysis fields: " + ", ".join(missing),
            "metrics": {"keys": len(payload), "missing": len(missing)},
        }
    return {
        "ok": True,
        "reason": None,
        "metrics": {"keys": len(payload), "missing": 0},
    }

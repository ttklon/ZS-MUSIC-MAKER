# -*- coding: utf-8 -*-
"""Лёгкие детерминированные проверки outputs локальных LLM-ролей.

Валидаторы не оценивают художественную ценность текста. Они отсекают только
объективно непригодные результаты: пустой/слишком короткий ответ, чрезмерные
дубли строк и неполное структурированное досье. Это позволяет честно включать
fallback до сохранения артефакта на диск.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9']+")


def lyrics_metrics(text: str) -> dict[str, float | int]:
    """Вернуть воспроизводимые метрики длины и повторяемости текста песни."""
    normalized_lines = [
        re.sub(r"\s+", " ", line.strip()).lower()
        for line in (text or "").splitlines()
        if line.strip() and not line.lstrip().startswith("[")
    ]
    tokens = TOKEN_RE.findall((text or "").lower())
    line_counts = Counter(normalized_lines)
    max_repeated_line = max(line_counts.values(), default=0)
    unique_ratio = len(set(tokens)) / len(tokens) if tokens else 0.0
    return {
        "characters": len((text or "").strip()),
        "lines": len(normalized_lines),
        "tokens": len(tokens),
        "unique_token_ratio": round(unique_ratio, 3),
        "max_repeated_line": max_repeated_line,
    }


def validate_lyrics(text: str, *, min_characters: int = 60) -> dict[str, Any]:
    """Проверить минимальную пригодность текста для следующей audio-стадии."""
    metrics = lyrics_metrics(text)
    if not (text or "").strip():
        return {"ok": False, "reason": "empty lyrics", "metrics": metrics}
    if metrics["characters"] < min_characters:
        return {
            "ok": False,
            "reason": f"lyrics shorter than {min_characters} characters",
            "metrics": metrics,
        }
    if metrics["tokens"] < 12:
        return {"ok": False, "reason": "too few lyric tokens", "metrics": metrics}
    # До четырёх повторов допустимы для припева; больше — признак зацикливания.
    if metrics["max_repeated_line"] > 4:
        return {"ok": False, "reason": "line repetition exceeds hook limit", "metrics": metrics}
    if metrics["unique_token_ratio"] < 0.12:
        return {"ok": False, "reason": "token diversity too low", "metrics": metrics}
    return {"ok": True, "reason": None, "metrics": metrics}


def validate_metadata_json(payload: Any) -> dict[str, Any]:
    """Проверить минимальный контракт метаданных релиза из metadata_llm."""
    if not isinstance(payload, dict):
        return {"ok": False, "reason": "metadata response is not an object", "metrics": {}}
    title = str(payload.get("title") or "").strip()
    descriptions = [str(payload.get(key) or "").strip() for key in ("spotify_desc", "youtube_desc")]
    missing = []
    if not 2 <= len(title) <= 120:
        missing.append("title")
    if not any(descriptions):
        missing.append("description")
    tag_count = sum(
        len(value) for key, value in payload.items()
        if key.startswith("tags_") and isinstance(value, list)
    )
    if tag_count == 0:
        missing.append("tags")
    if missing:
        return {
            "ok": False,
            "reason": "missing or invalid metadata fields: " + ", ".join(missing),
            "metrics": {"keys": len(payload), "tags": tag_count},
        }
    return {"ok": True, "reason": None, "metrics": {"keys": len(payload), "tags": tag_count}}


def audio_metrics(path: str | Path) -> dict[str, Any]:
    """Измерить базовые объективные показатели WAV/аудиофайла без ML."""
    try:
        import numpy as np
        import soundfile as sf

        samples, sample_rate = sf.read(str(path), always_2d=True)
    except Exception as exc:
        return {"readable": False, "reason": f"audio read failed: {exc}"}
    if samples.size == 0:
        return {"readable": False, "reason": "audio is empty"}
    peak = float(np.max(np.abs(samples)))
    rms = float(np.sqrt(np.mean(samples ** 2)))
    duration = len(samples) / sample_rate
    metrics = {
        "readable": True,
        "duration_sec": round(duration, 3),
        "sample_rate": int(sample_rate),
        "channels": int(samples.shape[1]),
        "peak": round(peak, 6),
        "rms": round(rms, 6),
    }
    if samples.shape[1] >= 2:
        left, right = samples[:, 0], samples[:, 1]
        denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
        correlation = float(np.dot(left, right) / denominator) if denominator > 1e-12 else 1.0
        metrics["stereo_correlation"] = round(correlation, 6)
        metrics["stereo_side_rms"] = round(float(np.sqrt(np.mean(((left - right) * 0.5) ** 2))), 6)
    return metrics


def validate_audio_artifact(path: str | Path, *, min_duration_sec: float = 1.0) -> dict[str, Any]:
    """Отсечь пустой, короткий, silent или клиппующий audio output."""
    target = Path(path)
    if not target.exists():
        return {"ok": False, "reason": "audio file missing", "metrics": {"path": str(target)}}
    metrics = audio_metrics(target)
    if not metrics.get("readable"):
        return {"ok": False, "reason": metrics.get("reason"), "metrics": metrics}
    if metrics["duration_sec"] < min_duration_sec:
        return {"ok": False, "reason": "audio duration below minimum", "metrics": metrics}
    if metrics["rms"] < 1e-5:
        return {"ok": False, "reason": "audio is silent", "metrics": metrics}
    if metrics["peak"] > 1.0001:
        return {"ok": False, "reason": "audio clips", "metrics": metrics}
    return {"ok": True, "reason": None, "metrics": metrics}


def validate_vocal_artifact(path: str | Path, text: str) -> dict[str, Any]:
    """Проверить, что синтезированный вокал существует и не слишком короток для текста."""
    token_count = len(TOKEN_RE.findall(text or ""))
    expected_min_duration = min(3.0, max(0.25, token_count * 0.05))
    result = validate_audio_artifact(path, min_duration_sec=expected_min_duration)
    result["metrics"]["text_tokens"] = token_count
    result["metrics"]["expected_min_duration_sec"] = round(expected_min_duration, 3)
    return result


def validate_rvc_artifact(input_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    """Проверить output RVC: аудио валидно и сохраняет временную структуру исходного вокала."""
    source = audio_metrics(input_path)
    if not source.get("readable"):
        return {"ok": False, "reason": "RVC input audio is unreadable", "metrics": {"input": source}}
    result = validate_audio_artifact(output_path, min_duration_sec=0.25)
    result["metrics"]["input_duration_sec"] = source.get("duration_sec")
    if not result["ok"]:
        return result
    input_duration = float(source["duration_sec"])
    output_duration = float(result["metrics"]["duration_sec"])
    ratio = output_duration / input_duration if input_duration > 0 else 0.0
    result["metrics"]["duration_ratio"] = round(ratio, 3)
    if not 0.85 <= ratio <= 1.15:
        return {"ok": False, "reason": "RVC output duration diverges from input", "metrics": result["metrics"]}
    return {"ok": True, "reason": None, "metrics": result["metrics"]}


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

    required = ("storyline", "hook", "reusable_elements") if track_level else (
        "core_themes",
        "lexicon",
        "flow",
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

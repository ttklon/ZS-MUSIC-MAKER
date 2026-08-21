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


def validate_song_lyrics(text: str, *, user_lines: list[str] | None = None,
                         min_words: int = 200, max_words: int = 800) -> dict[str, Any]:
    """Проверить release-структуру текста после базового lexical quality gate."""
    base = validate_lyrics(text, min_characters=60)
    metrics = dict(base["metrics"])
    lower = (text or "").lower()
    headers = [line.strip().lower() for line in (text or "").splitlines() if line.strip().startswith("[")]
    verse_headers = sum("куплет" in header or "verse" in header for header in headers)
    hook_headers = sum(any(marker in header for marker in ("припев", "hook", "chorus")) for header in headers)
    requested = [line.strip() for line in (user_lines or []) if line.strip()]
    included = [line for line in requested if line.lower() in lower]
    filler_terms = ("нейра-говно", "как ии", "language model", "as an ai")
    filler_hits = [term for term in filler_terms if term in lower]
    metrics.update({
        "words": metrics["tokens"],
        "verse_headers": verse_headers,
        "hook_headers": hook_headers,
        "user_lines_requested": len(requested),
        "user_lines_included": len(included),
        "filler_hits": filler_hits,
    })
    # Длинный structured текст закономерно повторяет служебные слова и hook.
    # Для release-form допускаем более низкую lexical diversity только при
    # сохранённом base repetition limit и последующих structure checks.
    if not base["ok"] and not (
        base["reason"] == "token diversity too low"
        and float(metrics["unique_token_ratio"]) >= 0.08
        and int(metrics["max_repeated_line"]) <= 4
    ):
        return {"ok": False, "reason": base["reason"], "metrics": metrics}
    if not min_words <= metrics["words"] <= max_words:
        return {"ok": False, "reason": "lyrics word count is outside release range", "metrics": metrics}
    if verse_headers < 2:
        return {"ok": False, "reason": "lyrics require at least two verses", "metrics": metrics}
    if hook_headers < 2:
        return {"ok": False, "reason": "lyrics require a repeated hook", "metrics": metrics}
    if len(included) != len(requested):
        return {"ok": False, "reason": "lyrics omit required user lines", "metrics": metrics}
    if filler_hits:
        return {"ok": False, "reason": "lyrics contain prohibited AI filler", "metrics": metrics}
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
        "dc_offset": round(float(np.max(np.abs(np.mean(samples, axis=0)))), 6),
    }
    if samples.shape[1] >= 2:
        left, right = samples[:, 0], samples[:, 1]
        denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
        correlation = float(np.dot(left, right) / denominator) if denominator > 1e-12 else 1.0
        metrics["stereo_correlation"] = round(correlation, 6)
        metrics["stereo_side_rms"] = round(float(np.sqrt(np.mean(((left - right) * 0.5) ** 2))), 6)
    return metrics


def master_audio_metrics(path: str | Path) -> dict[str, Any]:
    """Измерить пригодные для мастеринга уровни, включая 4x оценку true peak."""
    metrics = audio_metrics(path)
    if not metrics.get("readable"):
        return metrics
    try:
        import numpy as np
        import soundfile as sf

        samples, _ = sf.read(str(path), always_2d=True)
        peak = max(float(np.max(np.abs(samples))), 1e-12)
        rms = max(float(np.sqrt(np.mean(samples ** 2))), 1e-12)
        oversampled = samples
        try:
            from scipy.signal import resample_poly

            oversampled = resample_poly(samples, 4, 1, axis=0)
        except Exception:
            # Без scipy peak остаётся консервативной нижней оценкой true peak.
            pass
        true_peak = max(float(np.max(np.abs(oversampled))), 1e-12)
        metrics.update({
            "peak_dbfs": round(20.0 * float(np.log10(peak)), 3),
            "rms_dbfs": round(20.0 * float(np.log10(rms)), 3),
            "true_peak_dbtp": round(20.0 * float(np.log10(true_peak)), 3),
        })
        return metrics
    except Exception as exc:
        return {"readable": False, "reason": f"master metrics failed: {exc}"}


def validate_master_artifact(input_path: str | Path, output_path: str | Path, *,
                             max_true_peak_dbtp: float = -0.5,
                             min_rms_dbfs: float = -20.0,
                             max_rms_dbfs: float = -5.0) -> dict[str, Any]:
    """Проверить мастеринг: длину, stereo output, RMS-диапазон и true-peak ceiling."""
    source = audio_metrics(input_path)
    if not source.get("readable"):
        return {"ok": False, "reason": "master input audio is unreadable", "metrics": {"input": source}}
    base = validate_audio_artifact(output_path, min_duration_sec=0.25)
    base_metrics = base.get("metrics", {})
    base_metrics["input_duration_sec"] = source.get("duration_sec")
    if not base.get("ok"):
        return {"ok": False, "reason": base.get("reason"), "metrics": base_metrics}
    metrics = master_audio_metrics(output_path)
    metrics["input_duration_sec"] = source.get("duration_sec")
    if not metrics.get("readable"):
        return {"ok": False, "reason": metrics.get("reason"), "metrics": metrics}
    input_duration = float(source["duration_sec"])
    duration_ratio = float(metrics["duration_sec"]) / input_duration if input_duration > 0 else 0.0
    metrics["duration_ratio"] = round(duration_ratio, 3)
    if metrics.get("channels") != 2:
        return {"ok": False, "reason": "master is not stereo", "metrics": metrics}
    if not 0.95 <= duration_ratio <= 1.05:
        return {"ok": False, "reason": "master duration diverges from mix", "metrics": metrics}
    if float(metrics["true_peak_dbtp"]) > max_true_peak_dbtp:
        return {"ok": False, "reason": "master true peak exceeds ceiling", "metrics": metrics}
    if not min_rms_dbfs <= float(metrics["rms_dbfs"]) <= max_rms_dbfs:
        return {"ok": False, "reason": "master RMS is outside target range", "metrics": metrics}
    return {"ok": True, "reason": None, "metrics": metrics}


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
    if float(result["metrics"].get("dc_offset", 0.0)) > 0.02:
        return {"ok": False, "reason": "RVC output DC offset is too high", "metrics": result["metrics"]}
    return {"ok": True, "reason": None, "metrics": result["metrics"]}


def validate_cover_artifact(path: str | Path, *, min_size: int = 512,
                            min_bytes: int = 100) -> dict[str, Any]:
    """Проверить cover-art: файл существует, декодируется и соответствует минимальному разрешению."""
    target = Path(path)
    if not target.exists() or target.stat().st_size < min_bytes:
        return {
            "ok": False,
            "reason": "cover file is missing or below byte-size minimum",
            "metrics": {"path": str(target), "min_bytes": min_bytes},
        }
    try:
        from PIL import Image

        with Image.open(target) as image:
            image.verify()
        with Image.open(target) as image:
            width, height, mode = image.size[0], image.size[1], image.mode
    except Exception as exc:
        return {"ok": False, "reason": f"cover file is unreadable: {exc}", "metrics": {"path": str(target)}}
    metrics = {
        "width": int(width), "height": int(height), "mode": mode,
        "bytes": target.stat().st_size, "min_bytes": min_bytes,
    }
    if width < min_size or height < min_size:
        return {"ok": False, "reason": "cover resolution is below minimum", "metrics": metrics}
    if mode not in {"RGB", "RGBA"}:
        return {"ok": False, "reason": "cover color mode is unsupported", "metrics": metrics}
    return {"ok": True, "reason": None, "metrics": metrics}


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

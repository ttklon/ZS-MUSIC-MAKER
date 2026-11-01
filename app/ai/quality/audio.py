# -*- coding: utf-8 -*-
"""
app/ai/quality/audio.py — объективные проверки звуковых артефактов.

Только измеримое: длительность, клиппинг, тишина на краях, пиковый уровень,
соотношение каналов. Никакой «оценки на слух» — для неё есть отдельный
слепой протокол прослушивания.
"""

from __future__ import annotations

import logging

from pathlib import Path
from typing import Any

from app.ai.quality.lyrics import TOKEN_RE


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
            logging.getLogger(__name__).debug("ignored exception", exc_info=True)
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

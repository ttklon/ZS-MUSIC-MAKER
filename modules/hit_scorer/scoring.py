# -*- coding: utf-8 -*-
"""
modules/hit_scorer/scoring.py — взвешенная свёртка метрик в HitScore,
вердикт, рекомендации и главный API `score_track`.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

try:  # numpy нужен для проверки уровня; без него метрики и так отдают нейтрал
    import numpy as np
except Exception:  # pragma: no cover - зависит от окружения
    np = None  # type: ignore

from modules.hit_scorer.audio import HAS_LIBROSA, HAS_SF, _load_audio_cached
from modules.hit_scorer.mix_metrics import _metric_set


# ============================================================ verdict
_LOG = logging.getLogger(__name__)

WEIGHTS = {
    # Клиппинг слышен на всех площадках и не лечится после релиза, поэтому
    # вес выше среднего: раньше вдавленный в потолок трек получал те же
    # баллы, что чистый.
    "distortion": 1.3,
    "hook_energy": 1.5,
    "hook_repeatability": 1.3,
    "chorus_catchiness": 1.4,
    "drop_impact": 1.2,
    "tiktok_hookability": 1.5,
    "bpm_dance_fitness": 0.8,
    "loudness_lufs": 1.0,
    "stereo_width": 0.7,
    "low_end_power": 1.0,
    "vocal_presence": 1.1,
    "structure_clarity": 1.0,
    "novelty": 0.8,
}


def _level_dbfs(y) -> float:
    """RMS всего файла в dBFS. Без numpy считаем нейтральный ноль."""
    if np is None or y is None or len(y) == 0:
        return 0.0
    return 20.0 * float(np.log10(max(float(np.sqrt(np.mean(np.square(y)) + 1e-12)), 1e-12)))


def _invalid_audio_report(path: str, y, sr) -> dict:
    """Отчёт для файла, в котором нет звука: это не «плохой хит»."""
    return {
        "hit_score": 0.0,
        "verdict": "invalid_audio",
        "reason": f"в файле нет звука: RMS {_level_dbfs(y):.1f} dBFS",
        "metrics": {},
        "tiktok_slice": None,
        "actions": [],
        "meta": {"file": path, "duration_s": round(len(y) / sr, 2), "sr": sr},
    }


def _silence_guard(metrics: dict, y, sr) -> None:
    """Не давать баллы за «динамику», «новизну» и «низ», которых нет.

    Несколько метрик считают отношение двух почти-нулевых величин и на
    разреженном сигнале выдают максимум. Замер: один клик в 20 секундах
    тишины получал hook_energy 100, vocal_presence 100, novelty 100,
    low_end_power 92, а вместе — 61,85 и вердикт `needs_work`.

    Правило простое: если в окне почти нет энергии, метрика не может быть
    высокой — она ставится в ноль, а в подсказке сказано почему.
    """
    level = _level_dbfs(y)
    if level > -40.0:  # обычный трек: трогать нечего
        return
    for name in ("hook_energy", "novelty", "low_end_power", "vocal_presence"):
        if name in metrics and metrics[name]["score"] > 20.0:
            metrics[name]["score"] = 0.0
            metrics[name]["hint"] = (
                f"звука в файле почти нет: метрика не считается (RMS {level:.1f} dBFS)"
            )

# Что именно мерила метрика: раньше эти строки лежали в вызовах внутри
# `score_track` и съедали её бюджет длины.
_HINTS = {
    "hook_energy": "loud-quiet dynamic between chorus and verse",
    "hook_repeatability": "how many times main motif repeats",
    "chorus_catchiness": "harmonic simplicity + rhythmic regularity",
    "drop_impact": "biggest RMS jump = drop",
    "tiktok_hookability": "instant-hook 25 sec slice for TikTok",
    "bpm_dance_fitness": "BPM in dance/trap sweet spot",
    "loudness_lufs": "integrated dBFS ≈ LUFS streaming target",
    "stereo_width": "channel correlation 0.6-0.85",
    "low_end_power": "20-80 Hz vs 200-2000 Hz ratio",
    "vocal_presence": "2-5 kHz vocal readability",
    "structure_clarity": "distinct intro/verse/chorus/outro",
    "novelty": "non-formulaic spectral variety",
    "distortion": "clipping and flat tops at the ceiling",
}


def _verdict(score: float) -> str:
    if score >= 82.0:
        return "chart_ready"
    if score >= 68.0:
        return "solid"
    if score >= 50.0:
        return "needs_work"
    return "flop_risk"


# Готовая формулировка совета на каждую метрику: держать их отдельным
# словарём дешевле, чем лестницу elif в горячем пути отчёта.
_FIX_HINTS = {
    "hook_energy": (
        "Припев тише куплета — подними RMS припева на +2 dB "
        "или сделай drop громче"
    ),
    "hook_repeatability": "Повторяй главный мотив ≥3 раза (chorus/hook loop)",
    "chorus_catchiness": "Упрости гармонию припева до 2-3 аккордов, ритм — равномерные 4/4",
    "drop_impact": (
        "Добавь build-up (риз) перед drop и полусекунду тишины перед first-beat drop"
    ),
    "tiktok_hookability": (
        "Сделай моментальный вход в первые 2 сек (без длинного intro) — для TikTok/Reels"
    ),
    "bpm_dance_fitness": (
        "BPM вне dance-диапазонов. Целься в 120-140 (dance/phonk) или 70-95 (trap)"
    ),
    "loudness_lufs": (
        "LUFS вне streaming-target. Смастеринг под -9 dBFS интегрированной громкости"
    ),
    "stereo_width": (
        "Стерео-картинка слишком узкая или слишком широкая. Целься в correlation 0.6-0.85"
    ),
    "low_end_power": "Проработай sub-bass 20-80 Hz — добавь 808 или sub-sine",
    "vocal_presence": (
        "Вокал не читается в 2-5 kHz. Подними presence-полку +2 dB на 3 kHz"
    ),
    "structure_clarity": (
        "Секции слишком похожи. Добавь контраст между куплетом и припевом "
        "(плотность, элементы)"
    ),
    "novelty": (
        "Трек звучит формульно. Добавь уникальный саунд-дизайн элемент "
        "(FX, стоп, воб, риверс)"
    ),
}


def _actions(metrics: dict) -> list[str]:
    """Советы только по провалившимся метрикам, без повторов."""
    out = []
    for name, m in metrics.items():
        if m.get("score", 0.0) >= 65.0:
            continue
        hint = _FIX_HINTS.get(name) or _hint_for(name, m)
        if hint:
            out.append(hint)
    return out


def _hint_for(name: str, metric: dict) -> str:
    """Подсказки, которым нужны сырые значения метрики (не просто порог)."""
    if name != "distortion":
        return ""
    raw = metric.get("raw") or {}
    share = float(raw.get("clipped_share") or 0.0) * 100.0
    return (
        f"Клиппинг: {share:.1f}% сэмплов у потолка. Опусти лимитер на "
        "-1 dBTP и убери перегруз на шине — искажения слышны на всех площадках"
    )


def _build_report(*, path: str, hit_score: float, metrics: dict, slice_info, y, sr, elapsed: float) -> dict:
    """Собрать отчёт оценки: баллы, вердикт, подсказки и метаданные прогона."""
    return {
        "hit_score": round(hit_score, 2),
        "verdict": _verdict(hit_score),
        "metrics": metrics,
        "tiktok_slice": slice_info,
        "actions": _actions(metrics),
        "meta": {
            "file": path,
            "duration_s": round(len(y) / sr, 2),
            "sr": sr,
            "elapsed_s": elapsed,
            "librosa": HAS_LIBROSA,
            "soundfile": HAS_SF,
        },
    }


# ============================================================ main API
def score_track(master_wav: str, out_json: str | None = None, sr: int = 22050) -> dict:
    """
    Основной API. `master_wav` — путь к финальному мастеру.
    Возвращает полный отчёт. Если out_json — сохраняет.
    """
    t0 = time.time()
    p = Path(master_wav)
    if not p.exists():
        return {
            "error": f"file not found: {master_wav}",
            "hit_score": 0.0,
            "verdict": "flop_risk",
        }

    try:
        y, s = _load_audio_cached(str(p.resolve()), sr, p.stat().st_mtime_ns)
    except Exception as e:
        return {"error": f"load failed: {e}", "hit_score": 0.0, "verdict": "flop_risk"}

    # Пустой файл — это не «плохой хит», а отсутствие звука. Раньше тишина
    # получала 37 баллов и вердикт flop_risk: оценка делала вид, что слушала
    # трек.
    if _level_dbfs(y) < -60.0:
        report = _invalid_audio_report(str(p), y, s)
        if out_json:
            Path(out_json).write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        return report

    metrics = {}
    values = _metric_set(str(p), y, s)
    provenance = values.pop("_provenance")
    tt_slice = values.pop("_slice")
    for name, val in values.items():
        score, raw = val if isinstance(val, tuple) else (val, None)
        metrics[name] = {
            "score": round(float(score), 2),
            "raw": raw,
            "hint": _HINTS.get(name, ""),
        }
    for name, prov in provenance.items():
        if name in metrics:
            metrics[name]["provenance"] = prov

    _silence_guard(metrics, y, s)

    # weighted total
    total_w = sum(WEIGHTS.values())
    hit_score = sum(metrics[k]["score"] * WEIGHTS[k] for k in WEIGHTS) / total_w

    report = _build_report(
        path=str(p), hit_score=hit_score, metrics=metrics, slice_info=tt_slice,
        y=y, sr=s, elapsed=round(time.time() - t0, 2),
    )

    if out_json:
        Path(out_json).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return report

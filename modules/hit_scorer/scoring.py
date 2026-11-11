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
from modules.hit_scorer.hook_metrics import (
    _bpm_dance_fitness,
    _chorus_catchiness,
    _drop_impact,
    _hook_energy,
    _hook_repeatability,
    _tiktok_hookability,
)
from modules.hit_scorer.mix_metrics import (
    _loudness_lufs_status,
    _low_end_power,
    _novelty,
    _stereo_width,
    _structure_clarity,
    _vocal_presence,
)


# ============================================================ verdict
_LOG = logging.getLogger(__name__)

WEIGHTS = {
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


def _verdict(score: float) -> str:
    if score >= 82.0:
        return "chart_ready"
    if score >= 68.0:
        return "solid"
    if score >= 50.0:
        return "needs_work"
    return "flop_risk"


def _actions(metrics: dict) -> list[str]:
    out = []
    for name, m in metrics.items():
        s = m.get("score", 0.0)
        if s >= 65.0:
            continue
        if name == "hook_energy":
            out.append(
                "Припев тише куплета — подними RMS припева на +2 dB "
                "или сделай drop громче"
            )
        elif name == "hook_repeatability":
            out.append("Повторяй главный мотив ≥3 раза (chorus/hook loop)")
        elif name == "chorus_catchiness":
            out.append(
                "Упрости гармонию припева до 2-3 аккордов, ритм — " "равномерные 4/4"
            )
        elif name == "drop_impact":
            out.append(
                "Добавь build-up (риз) перед drop и полусекунду тишины "
                "перед first-beat drop"
            )
        elif name == "tiktok_hookability":
            out.append(
                "Сделай моментальный вход в первые 2 сек (без длинного "
                "intro) — для TikTok/Reels"
            )
        elif name == "bpm_dance_fitness":
            out.append(
                "BPM вне dance-диапазонов. Целься в 120-140 "
                "(dance/phonk) или 70-95 (trap)"
            )
        elif name == "loudness_lufs":
            out.append(
                "LUFS вне streaming-target. Смастеринг под -9 dBFS "
                "интегрированной громкости"
            )
        elif name == "stereo_width":
            out.append(
                "Стерео-картинка слишком узкая или слишком широкая. "
                "Целься в correlation 0.6-0.85"
            )
        elif name == "low_end_power":
            out.append("Проработай sub-bass 20-80 Hz — добавь 808 или " "sub-sine")
        elif name == "vocal_presence":
            out.append(
                "Вокал не читается в 2-5 kHz. Подними presence-полку " "+2 dB на 3 kHz"
            )
        elif name == "structure_clarity":
            out.append(
                "Секции слишком похожи. Добавь контраст между "
                "куплетом и припевом (плотность, элементы)"
            )
        elif name == "novelty":
            out.append(
                "Трек звучит формульно. Добавь уникальный саунд-дизайн "
                "элемент (FX, стоп, воб, риверс)"
            )
    return out


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

    metrics = {}

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

    def _add(name, val_tuple, hint=""):
        score, raw = val_tuple if isinstance(val_tuple, tuple) else (val_tuple, None)
        metrics[name] = {"score": round(float(score), 2), "raw": raw, "hint": hint}

    _add(
        "hook_energy", _hook_energy(y, s), "loud-quiet dynamic between chorus and verse"
    )
    _add(
        "hook_repeatability",
        _hook_repeatability(y, s),
        "how many times main motif repeats",
    )
    _add(
        "chorus_catchiness",
        _chorus_catchiness(y, s),
        "harmonic simplicity + rhythmic regularity",
    )
    _add("drop_impact", _drop_impact(y, s), "biggest RMS jump = drop")
    tt_score, tt_slice = _tiktok_hookability(y, s)
    _add(
        "tiktok_hookability",
        (tt_score, tt_slice),
        "instant-hook 25 sec slice for TikTok",
    )
    _add("bpm_dance_fitness", _bpm_dance_fitness(y, s), "BPM in dance/trap sweet spot")
    loudness_result, loudness_provenance = _loudness_lufs_status(y, s)
    _add(
        "loudness_lufs", loudness_result, "integrated dBFS ≈ LUFS streaming target"
    )
    metrics["loudness_lufs"]["provenance"] = loudness_provenance
    _add("stereo_width", _stereo_width(str(p)), "channel correlation 0.6-0.85")
    _add("low_end_power", _low_end_power(y, s), "20-80 Hz vs 200-2000 Hz ratio")
    _add("vocal_presence", _vocal_presence(y, s), "2-5 kHz vocal readability")
    _add(
        "structure_clarity",
        _structure_clarity(y, s),
        "distinct intro/verse/chorus/outro",
    )
    _add("novelty", _novelty(y, s), "non-formulaic spectral variety")

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

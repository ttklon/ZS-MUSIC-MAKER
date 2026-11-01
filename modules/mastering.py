# -*- coding: utf-8 -*-
"""modules/mastering.py — единственный мастеринг проекта (план 4.6).

Цепочка: коррекция тона под стенд → двухполосная компрессия → look-ahead
лимитер с потолком −1 dBTP → сходимость по LUFS. Всё измеряется настоящими
метриками (`modules.dsp.metrics`), а не «на слух»:

* true peak — 4× oversample (≤ −1.0 dBTP на каждом стенде);
* LUFS — pyloudnorm (ITU-R BS.1770), с явным статусом, если его нет;
* клиппинг — 0 сэмплов; корреляция и потеря в моно — гейты §7.2.

`master_all_stands` пишет `master_<stand>.wav` и возвращает отчёт с гейтами
по каждому стенду. Недостижимая цель (например, клуб −8.5 LUFS на очень
динамичном миксе) не выдаётся за успех: `gates[lufs] = False` и в отчёте
стоит фактическое значение.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from modules.dsp import dynamics, filters, limiter, metrics

_LOG = logging.getLogger(__name__)

__all__ = [
    "ALL_STANDS",
    "STAND_TARGET_LUFS",
    "master_all_stands",
    "master_one",
    "normalize_master_loudness",
]

TRUE_PEAK_CEILING = -1.0

# Целевые LUFS по стендам (§7.2: streaming −14 ± 0.5, клуб/тачка −8…−9).
STAND_TARGET_LUFS: dict[str, float] = {
    "streaming": -14.0,
    "tiktok": -11.5,
    "club": -8.5,
    "car": -10.0,
    "airpods": -14.0,
    "bluetooth": -14.5,
    "headphones": -14.0,
    "monitors": -14.0,
}

LUFS_TOLERANCE: dict[str, float] = {
    "streaming": 0.5,
    "tiktok": 0.6,
    "club": 0.5,  # −9…−8
    "car": 0.7,
    "airpods": 0.5,
    "bluetooth": 0.7,
    "headphones": 0.5,
    "monitors": 0.5,
}

# Crest-коридор зависит от стенда: клубные мастера плотнее по определению.
CREST_RANGE: dict[str, tuple[float, float]] = {
    # Клубный мастер по определению плотный: −8.5 LUFS при −1 dBTP не бывает
    # с «живым» крестом 8–14 дБ (это гейт микса, а не мастера).
    "club": (4.0, 11.0),
    "car": (5.5, 12.0),
    "tiktok": (6.0, 13.0),
}
DEFAULT_CREST = (8.0, 14.0)

# Характер стенда: (срез Гц, дБ, полоса) — та же логика, что была, но через dsp.
STAND_EQ: dict[str, tuple[tuple[float, float, str], ...]] = {
    "streaming": ((150, 0.5, "low"), (8000, 1.0, "high")),
    "car": ((120, 1.5, "low"), (6500, 1.0, "high")),
    "club": ((100, 2.5, "low"), (9000, 0.5, "high")),
    "tiktok": ((200, 1.0, "low"), (7500, 2.0, "high")),
    "airpods": ((250, 1.0, "low"), (8000, 1.5, "high")),
    "bluetooth": ((180, 1.5, "low"), (7000, 1.0, "high")),
    "headphones": ((150, 0.5, "low"), (9000, 0.5, "high")),
    "monitors": ((150, 0.0, "low"), (10000, 0.0, "high")),
}

ALL_STANDS = list(STAND_TARGET_LUFS)

# Совместимость: старый публичный словарь dBFS-ориентиров.
STAND_TARGET_DBFS: dict[str, float] = {}


def _load(path: str | Path) -> tuple[np.ndarray, int]:
    data, sr = sf.read(str(path), always_2d=True)
    y = np.asarray(data, dtype=np.float64)
    if y.ndim == 2 and y.shape[1] == 1:
        y = np.repeat(y, 2, axis=1)
    return y, int(sr)


def _tone(y: np.ndarray, sample_rate: int, stand: str) -> np.ndarray:
    out = y
    for cutoff, gain_db, band in STAND_EQ.get(stand, STAND_EQ["streaming"]):
        if abs(gain_db) > 1e-6:
            out = filters.shelf(out, sample_rate, cutoff, gain_db, band)
    return out


def _render_candidate(
    base: np.ndarray,
    sample_rate: int,
    gain_db: float,
    ceiling_dbtp: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Один проход «усиление → мягкий клиппер → лимитер → правка ширины»."""
    from modules.mix.width import match_width

    candidate = base * (10.0 ** (gain_db / 20.0))
    info: dict[str, Any] = {"gain_db": round(float(gain_db), 2)}
    # Клиппер применяется всегда, но ниже колена (= потолка) он математически
    # ничего не меняет. Включать его «по условию» нельзя: на границе включения
    # громкость скачет на несколько дБ и калибровка теряет устойчивость.
    candidate, info["soft_clip"] = limiter.soft_clip(candidate, knee_dbfs=ceiling_dbtp)
    candidate, info["limiter"] = limiter.limit(candidate, sample_rate, ceiling_dbtp=ceiling_dbtp)
    candidate, width_info = match_width(candidate)
    if width_info.get("width", 1.0) != 1.0:
        candidate, info["relimiter"] = limiter.limit(
            candidate, sample_rate, ceiling_dbtp=ceiling_dbtp
        )
    info["width"] = width_info
    return candidate, info


def _converge_loudness(
    y: np.ndarray,
    sample_rate: int,
    target_lufs: float,
    *,
    ceiling_dbtp: float = TRUE_PEAK_CEILING,
    tolerance: float = 0.25,
    max_gain_db: float = 18.0,
    search_iterations: int = 6,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Довести трек до целевого LUFS устойчиво, без «качелей».

    Отклик громкости на усиление нелинейный (после включения клиппера он резко
    растёт), поэтому итеративное «gain += ошибка» раскачивается. Вместо этого:

    1. калибровка на громком 30-секундном фрагменте — бисекция по усилению;
    2. рендер всего трека найденным усилением;
    3. до трёх поправок по фактическому интегрированному LUFS с запоминанием
       лучшего результата.

    Недостижимая цель (клуб на очень динамичном миксе) не дотягивается
    перегрузом: в отчёте остаются фактическая громкость и признак
    `limiter_saturated`.
    """
    excerpt = metrics.active_window(y, sample_rate, 30.0)
    has_excerpt = excerpt.shape[0] < y.shape[0]

    def measure_gain(gain_db: float) -> float:
        source = excerpt if has_excerpt else y
        rendered, _ = _render_candidate(source, sample_rate, gain_db, ceiling_dbtp)
        return float(metrics.integrated_lufs(rendered, sample_rate)[0])

    low, high = 0.0, max_gain_db
    best_gain = 0.0
    best_err = abs(measure_gain(0.0) - target_lufs)
    top_lufs = measure_gain(high)
    if abs(top_lufs - target_lufs) < best_err:
        best_gain, best_err = high, abs(top_lufs - target_lufs)
    saturated = top_lufs < target_lufs
    if not saturated:
        for _ in range(search_iterations):
            middle = (low + high) * 0.5
            lufs = measure_gain(middle)
            err = abs(lufs - target_lufs)
            if err < best_err:
                best_gain, best_err = middle, err
            if lufs < target_lufs:
                low = middle
            else:
                high = middle
            if err <= tolerance:
                break

    rendered, render_info = _render_candidate(y, sample_rate, best_gain, ceiling_dbtp)
    lufs, metering = metrics.integrated_lufs(rendered, sample_rate)
    # Финальная доводка с учётом физики: чтобы стать громче, нужен новый рендер
    # с большим усилением (свежий клиппинг), чтобы стать тише — достаточно
    # линейного трима уже готового мастера. Оба шага принимаются только если
    # стали ближе к цели.
    corrections = 0
    for _ in range(4):
        err = target_lufs - lufs
        if abs(err) <= tolerance:
            break
        corrections += 1
        if err > 0:
            trial, trial_info = _render_candidate(
                y, sample_rate, min(best_gain + err, max_gain_db), ceiling_dbtp
            )
            trial_lufs, trial_metering = metrics.integrated_lufs(trial, sample_rate)
        else:
            trial, _ = limiter.limit(
                rendered * (10.0 ** (err / 20.0)), sample_rate, ceiling_dbtp=ceiling_dbtp
            )
            trial_info = {}
            trial_lufs, trial_metering = metrics.integrated_lufs(trial, sample_rate)
        if abs(target_lufs - trial_lufs) < abs(target_lufs - lufs) - 0.01:
            rendered, lufs, metering = trial, trial_lufs, trial_metering
            render_info.update(trial_info)
            if err > 0:
                best_gain = min(best_gain + err, max_gain_db)
            else:
                render_info["trim_db"] = round(float(err), 2)
        else:
            break
    if abs(target_lufs - lufs) > tolerance:
        saturated = True  # громкость вышла на предел: честно фиксируем факт
    return rendered, {
        "target_lufs": target_lufs,
        "achieved_lufs": round(float(lufs), 2),
        "error_lu": round(float(lufs - target_lufs), 2),
        "gain_applied_db": round(float(best_gain), 2),
        "corrections": corrections,
        "limiter_saturated": saturated,
        **{k: v for k, v in render_info.items() if k != "gain_db"},
        **metering,
    }


def _gates(report: dict[str, Any], stand: str) -> dict[str, bool]:
    lufs = float(report["lufs"])
    target = STAND_TARGET_LUFS.get(stand, -14.0)
    tol = LUFS_TOLERANCE.get(stand, 0.5)
    crest_lo, crest_hi = CREST_RANGE.get(stand, DEFAULT_CREST)
    corr = float(report["stereo_correlation"]) if int(report["channels"]) > 1 else 0.5
    return {
        "true_peak": float(report["true_peak_dbtp"]) <= TRUE_PEAK_CEILING,
        "lufs": abs(lufs - target) <= tol,
        "crest": crest_lo <= float(report["crest_db"]) <= crest_hi,
        "correlation": 0.2 <= corr <= 0.8,
        "mono_loss": float(report["mono_loss_db"]) <= 3.0,
        "no_clipping": int(report["clipping_samples"]) == 0,
    }


def master_one(mix_wav: str, out_wav: str, stand: str = "streaming") -> dict[str, Any]:
    """Мастеринг одного WAV под конкретный стенд. Всегда стерео, всегда с отчётом."""
    try:
        y, sr = _load(mix_wav)
    except Exception as exc:
        return {"ok": False, "reason": f"read failed: {type(exc).__name__}: {exc}"}
    if y.size == 0:
        return {"ok": False, "reason": "input mix is empty"}

    target = STAND_TARGET_LUFS.get(stand, STAND_TARGET_LUFS["streaming"])
    y = _tone(y, sr, stand)
    compressed, comp_info = dynamics.multiband_compress(
        y, sr, split_hz=190.0,
        low={"threshold_db": -14.0, "ratio": 1.6, "attack_ms": 25.0, "release_ms": 200.0},
        high={"threshold_db": -20.0, "ratio": 1.4, "attack_ms": 10.0, "release_ms": 120.0},
    )
    mastered, loudness_info = _converge_loudness(compressed, sr, target)
    mastered = np.nan_to_num(mastered, nan=0.0, posinf=0.0, neginf=0.0)
    report = metrics.loudness_report(mastered, sr)
    gates = _gates(report, stand)
    advice = None
    if not gates["lufs"]:
        advice = (
            f"цель {target} LUFS недостижима без перегруза: получено {report['lufs']} LUFS. "
            "Сведите микс плотнее (crest опорного участка ≤ 10.5 дБ) или выберите более тихий стенд"
        )

    out = Path(out_wav)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), mastered.astype(np.float32), sr, subtype="FLOAT")

    return {
        "ok": True,
        "path": str(out),
        "stand": stand,
        "channels": report["channels"],
        "sample_rate": sr,
        "target_lufs": target,
        "input_lufs": round(float(metrics.integrated_lufs(y, sr)[0]), 2),
        "output_lufs": report["lufs"],
        "output_true_peak_dbtp": report["true_peak_dbtp"],
        "output_peak_db": report["peak_dbfs"],
        "crest_db": report["crest_db"],
        "compression": comp_info,
        "width": loudness_info.get("width", {}),
        "loudness": loudness_info,
        "lufs_engine": report["lufs_engine"],
        "lufs_status": report["lufs_status"],
        "report": report,
        "gates": gates,
        "gates_passed": all(gates.values()),
        "advice": advice,
        "fallback_used": False,
    }


def normalize_master_loudness(
    input_wav: str,
    output_wav: str | None = None,
    target_lufs: float = -14.0,
    ceiling_db: float = TRUE_PEAK_CEILING,
) -> dict[str, Any]:
    """Довести громкость уже готового мастера без новой DSP-окраски."""
    output_wav = output_wav or input_wav
    try:
        y, sr = _load(input_wav)
    except Exception as exc:
        return {"ok": False, "reason": f"read failed: {type(exc).__name__}: {exc}"}
    if y.size == 0:
        return {"ok": False, "reason": "master audio is empty"}

    normalized, info = _converge_loudness(y, sr, target_lufs, ceiling_dbtp=ceiling_db)
    report = metrics.loudness_report(normalized, sr)
    out = Path(output_wav)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), normalized.astype(np.float32), sr, subtype="FLOAT")
    return {
        "ok": True,
        "path": str(out),
        "target_lufs": float(target_lufs),
        "output_lufs": report["lufs"],
        "output_true_peak_dbtp": report["true_peak_dbtp"],
        "output_peak_db": report["peak_dbfs"],  # совместимость с прежним API
        "output_rms_dbfs": report["rms_dbfs"],
        "loudness_mode": "integrated_lufs" if report["lufs_status"] == "ok" else "rms_approximation",
        "sample_rate": sr,
        "channels": report["channels"],
        "report": report,
        "loudness": info,
    }


def master_all_stands(
    mix_wav: str,
    out_dir: str,
    stands: list[str] | None = None,
) -> dict[str, Any]:
    """Мастеринг под все запрошенные стенды + сводный отчёт по гейтам."""
    chosen = stands or ALL_STANDS
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    masters: dict[str, str] = {}
    reports: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}
    for stand in chosen:
        result = master_one(mix_wav, str(out / f"master_{stand}.wav"), stand=stand)
        if result.get("ok"):
            masters[stand] = str(result["path"])
            reports[stand] = result
        else:
            errors[stand] = str(result.get("reason", "unknown"))

    failed_gates = {
        stand: [name for name, ok in data["gates"].items() if not ok]
        for stand, data in reports.items()
        if not data["gates_passed"]
    }
    summary = {
        "total": len(chosen),
        "done": len(masters),
        "fallback": 0,
        "errors": errors,
        "gates_passed": all(data["gates_passed"] for data in reports.values()) if reports else False,
        "failed_gates": failed_gates,
    }
    payload: dict[str, Any] = {
        "ok": bool(masters),
        "masters": masters,
        "reports": {stand: data["report"] for stand, data in reports.items()},
        "summary": summary,
    }
    report_path = out / "mastering_report.json"
    report_path.write_text(
        json.dumps(
            {
                "standards": {s: STAND_TARGET_LUFS[s] for s in chosen if s in STAND_TARGET_LUFS},
                "reports": payload["reports"],
                "gates": {stand: data["gates"] for stand, data in reports.items()},
                "failed_gates": failed_gates,
                "summary": summary,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    payload["report_path"] = str(report_path)
    return payload


def _cli(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: python -m modules.mastering <mix.wav> <out_dir> [stand]")
        return 2
    mix_wav, out_dir = argv[1], argv[2]
    stands = [argv[3]] if len(argv) > 3 else None
    result = master_all_stands(mix_wav, out_dir, stands=stands)
    print(json.dumps(result.get("summary", result), ensure_ascii=False, indent=2))
    return 0 if result.get("summary", {}).get("gates_passed") else 1


if __name__ == "__main__":  # pragma: no cover
    import sys

    raise SystemExit(_cli(sys.argv))

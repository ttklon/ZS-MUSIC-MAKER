# -*- coding: utf-8 -*-
"""modules/mastering/chain.py — цепь мастеринга одного стенда.

Тон под стенд → двухполосная компрессия → сходимость по LUFS → правка crest
→ финальный замер и гейты. `master_one` — единственная точка, где рождается
готовый `master_<stand>.wav`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from modules.dsp import dynamics, filters, limiter, metrics
from modules.mastering.loudness import _converge_loudness
from modules.mastering.targets import (
    CORRELATION_RANGE,
    CREST_RANGE,
    DEFAULT_CORRELATION,
    DEFAULT_CREST,
    LUFS_TOLERANCE,
    STAND_EQ,
    STAND_TARGET_LUFS,
    TRUE_PEAK_CEILING,
)


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


def _control_crest(
    mastered: np.ndarray,
    source: np.ndarray,
    sample_rate: int,
    stand: str,
    target_lufs: float,
    ceiling_dbtp: float = TRUE_PEAK_CEILING,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Довести crest-фактор мастера в коридор стенда — измеримо, без магии.

    Коридор снизу уже удержан при сведении громкости (кандидаты с crest ниже
    нормы отбрасываются). Здесь остаётся «слишком живой» мастер: пики
    аккуратно подрезаются мягким клиппером (нелинейно — в отличие от
    лимитера, который масштабирует весь сигнал и crest не меняет), после чего
    громкость возвращается к цели. Каждый шаг пишется в отчёт.
    """
    low, high = CREST_RANGE.get(stand, DEFAULT_CREST)
    crest = float(metrics.loudness_report(mastered, sample_rate)["crest_db"])
    info: dict[str, Any] = {
        "crest_before_db": round(crest, 2),
        "corridor_db": [low, high],
        "actions": [],
    }
    for offset in (1.0, 2.0, 3.0, 4.0, 5.0):
        if crest <= high:
            break
        clipped, _ = limiter.soft_clip(mastered, knee_dbfs=ceiling_dbtp - offset)
        lufs = float(metrics.integrated_lufs(clipped, sample_rate)[0])
        gain_db = float(np.clip(target_lufs - lufs, -6.0, 6.0))
        restored, _ = limiter.soft_clip(
            clipped * (10.0 ** (gain_db / 20.0)), knee_dbfs=ceiling_dbtp
        )
        # мягкий клиппер может выйти за потолок: финальный лимитер обязателен
        restored, _ = limiter.limit(restored, sample_rate, ceiling_dbtp=ceiling_dbtp)
        new_crest = float(metrics.loudness_report(restored, sample_rate)["crest_db"])
        info["actions"].append(f"soft_clip_knee_-{offset}_db")
        if new_crest < crest:
            mastered, crest = restored, new_crest
    if crest > high:
        # тяжёлый лимитер держит пики, но не сжимает тело: чтобы убрать
        # избыточный crest, нужна компрессия, а не ещё один лимитер
        from modules.dsp import dynamics

        compressed, comp_info = dynamics.compress(
            mastered,
            sample_rate,
            threshold_db=-14.0,
            ratio=2.5,
            attack_ms=5.0,
            release_ms=120.0,
        )
        lufs = float(metrics.integrated_lufs(compressed, sample_rate)[0])
        gain_db = float(np.clip(target_lufs - lufs, -6.0, 6.0))
        restored, _ = limiter.limit(
            compressed * (10.0 ** (gain_db / 20.0)),
            sample_rate,
            ceiling_dbtp=ceiling_dbtp,
        )
        new_crest = float(metrics.loudness_report(restored, sample_rate)["crest_db"])
        info["actions"].append("compress_body_ratio_2_5")
        info["compressor"] = comp_info
        if new_crest < crest:
            mastered, crest = restored, new_crest

    if crest < low - 0.05:
        info["below_floor"] = True
        info["reason"] = (
            "crest ниже коридора: цель по громкости требует плотнее, чем позволяет материал"
        )
    info["crest_after_db"] = round(crest, 2)
    return mastered, info


def _gates(report: dict[str, Any], stand: str) -> dict[str, bool]:
    lufs = float(report["lufs"])
    target = STAND_TARGET_LUFS.get(stand, -14.0)
    tol = LUFS_TOLERANCE.get(stand, 0.5)
    crest_lo, crest_hi = CREST_RANGE.get(stand, DEFAULT_CREST)
    corr = float(report["stereo_correlation"]) if int(report["channels"]) > 1 else 0.5
    corr_lo, corr_hi = CORRELATION_RANGE.get(stand, DEFAULT_CORRELATION)
    return {
        "true_peak": float(report["true_peak_dbtp"]) <= TRUE_PEAK_CEILING,
        "lufs": abs(lufs - target) <= tol,
        "crest": crest_lo <= float(report["crest_db"]) <= crest_hi,
        "correlation": corr_lo <= corr <= corr_hi,
        "mono_loss": float(report["mono_loss_db"]) <= 3.0,
        "no_clipping": int(report["clipping_samples"]) == 0,
    }


def master_one(
    mix_wav: str,
    out_wav: str,
    stand: str = "streaming",
    iterations: int | None = None,
) -> dict[str, Any]:
    """Мастеринг одного WAV под конкретный стенд. Всегда стерео, всегда с отчётом.

    `iterations` — сколько доводок громкости делал `_converge_loudness`
    (режим качества из визарда). `None` — прежнее поведение (6 итераций),
    поэтому вызовы без аргумента считают бит-в-бит как раньше.
    """
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
    crest_low, crest_high = CREST_RANGE.get(stand, DEFAULT_CREST)
    # Режим качества задаёт глубину поиска во всех доводках этого стенда,
    # включая rescue/topup: иначе "fast" всё равно тратил бы полный бюджет.
    search_iterations = max(1, int(iterations)) if iterations else 6
    mastered, loudness_info = _converge_loudness(
        compressed,
        sr,
        target,
        min_crest_db=crest_low,
        max_crest_db=crest_high,
        search_iterations=search_iterations,
    )
    # Если цель по громкости не достигнута из-за транзиентов (лимитер уже стоит
    # на потолке, а прибавка усиления не даёт LUFS), единственный честный путь —
    # уменьшить динамический диапазон тела, а не задирать усиление.
    rescue_attempts: list[dict[str, Any]] = []
    source = compressed
    for _ in range(2):
        if not loudness_info.get("limiter_saturated"):
            break
        source, _comp_info = dynamics.compress(
            source,
            sr,
            threshold_db=-18.0,
            ratio=2.0,
            attack_ms=10.0,
            release_ms=150.0,
        )
        mastered, loudness_info = _converge_loudness(
            source,
            sr,
            target,
            min_crest_db=crest_low,
            max_crest_db=crest_high,
            search_iterations=search_iterations,
        )
        rescue_attempts.append(
            {
                "achieved_lufs": loudness_info.get("achieved_lufs"),
                "saturated": loudness_info.get("limiter_saturated"),
            }
        )
    if rescue_attempts:
        loudness_info["loudness_rescue"] = rescue_attempts
    mastered, crest_info = _control_crest(mastered, compressed, sr, stand, target)
    # Правка плотности (клиппер/компрессор) может уронить громкость: добираем её
    # обратно уже на готовом сигнале, по-прежнему не выходя из crest-коридора.
    current_lufs = float(metrics.integrated_lufs(mastered, sr)[0])
    topup_info: dict[str, Any] | None = None
    if abs(current_lufs - target) > 0.25:
        mastered, topup_info = _converge_loudness(
            mastered,
            sr,
            target,
            max_gain_db=4.0,
            min_crest_db=crest_low,
            max_crest_db=crest_high,
            search_iterations=search_iterations,
        )
        crest_info["topup"] = {
            "lufs_before": round(current_lufs, 2),
            "lufs_after": topup_info.get("achieved_lufs"),
            "gain_db": topup_info.get("gain_applied_db"),
        }
    loudness_info["crest_control"] = crest_info
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

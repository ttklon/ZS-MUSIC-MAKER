# -*- coding: utf-8 -*-
"""modules/mix/width.py — стерео-ширина через mid/side (план 4.5.3).

Почему не Haas: задержка одного канала даёт фазовые проблемы и «развал» в моно.
Mid/side масштабирует только боковую составляющую — моно-сумма остаётся целой,
а корреляция управляема и измерима.

`match_width` подбирает ширину так, чтобы корреляция микса попала в коридор
0.2…0.8 из §7.2. Это детерминированный бинарный поиск, без «на глаз».
"""

from __future__ import annotations

import numpy as np

from modules.dsp.metrics import mono_loss_db, stereo_correlation

__all__ = ["apply_width", "match_width", "mid_side", "stereo_report"]

MIN_CORRELATION = 0.2
MAX_CORRELATION = 0.8


def mid_side(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Разложить стерео на `(mid, side)`. Моно-вход → side = 0."""
    arr = np.asarray(x, dtype=np.float64)
    if arr.ndim == 1 or arr.shape[1] < 2:
        mono = arr if arr.ndim == 1 else arr[:, 0]
        return mono, np.zeros_like(mono)
    mid = (arr[:, 0] + arr[:, 1]) * 0.5
    side = (arr[:, 0] - arr[:, 1]) * 0.5
    return mid, side


def apply_width(x: np.ndarray, width: float) -> np.ndarray:
    """Масштабировать side на `width` (1.0 = как есть, 0.0 = моно)."""
    arr = np.asarray(x, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] < 2:
        return arr
    mid, side = mid_side(arr)
    side = side * float(max(width, 0.0))
    return np.stack([mid + side, mid - side], axis=1)


def stereo_report(x: np.ndarray) -> dict[str, float]:
    """Измерить корреляцию, относительную ширину и потерю в моно."""
    arr = np.asarray(x, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] < 2 or arr.size == 0:
        return {"correlation": 1.0, "side_to_mid_db": -120.0, "mono_loss_db": 0.0}
    mid, side = mid_side(arr)
    mid_rms = float(np.sqrt(np.mean(mid**2)))
    side_rms = float(np.sqrt(np.mean(side**2)))
    ratio = 20.0 * np.log10(max(side_rms, 1e-12) / max(mid_rms, 1e-12))
    return {
        "correlation": round(stereo_correlation(arr), 3),
        "side_to_mid_db": round(float(ratio), 2),
        "mono_loss_db": round(mono_loss_db(arr), 2),
    }


def match_width(
    x: np.ndarray,
    *,
    min_correlation: float = MIN_CORRELATION,
    max_correlation: float = MAX_CORRELATION,
    max_width: float = 2.0,
) -> tuple[np.ndarray, dict[str, float | bool]]:
    """Подобрать ширину так, чтобы корреляция попала в коридор.

    Возвращает `(out, report)` с `matched` — попали ли в коридор. Если сигнал
    изначально полностью моно, расширять нечего: честно `matched=False`,
    ошибка не выдумывается (моно-трек не «разваливаем» искусственно).
    """
    arr = np.asarray(x, dtype=np.float64)
    base = stereo_correlation(arr)
    mid, side = mid_side(arr)
    mid_rms = float(np.sqrt(np.mean(mid**2))) if mid.size else 0.0
    side_rms = float(np.sqrt(np.mean(side**2))) if side.size else 0.0
    report: dict[str, float | bool | str] = {
        "correlation_before": round(base, 3),
        "width": 1.0,
        "mono_loss_db": round(mono_loss_db(arr), 2),
        "matched": min_correlation <= base <= max_correlation,
    }
    if mid_rms > 1e-9 and side_rms / mid_rms < 1e-4:
        # Моно-источник: боковой составляющей нет, расширять нечего. Ширину
        # нельзя «изобрести» mid/side-масштабированием — честно говорим об этом.
        report["correlation_after"] = round(base, 3)
        report["reason"] = "mono source: no side content to widen"
        report["matched"] = False
        return arr, report
    if arr.ndim != 2 or arr.shape[1] < 2 or report["matched"]:
        report["correlation_after"] = round(base, 3)
        if not report["matched"]:
            report["reason"] = "source has no stereo pair (mono/1-D input)"
        return arr, report

    # Корреляция монотонно убывает с ростом ширины (при положительной базе),
    # поэтому бинарный поиск по ширине сходится к границе коридора.
    target = min(max(base, min_correlation), max_correlation)
    best_width = 1.0
    best_corr = base
    best_err = abs(base - target)
    lo, hi = 0.0, max_width
    for _ in range(14):
        mid = (lo + hi) * 0.5
        corr = stereo_correlation(apply_width(arr, mid))
        err = abs(corr - target)
        if err < best_err:
            best_width, best_corr, best_err = mid, corr, err
        if min_correlation <= corr <= max_correlation:
            best_width, best_corr, best_err = mid, corr, err
            break
        if corr > max_correlation:
            lo = mid  # мало ширины — расширяем
        else:
            hi = mid  # слишком широко — сужаем

    out = apply_width(arr, best_width)
    report["width"] = round(best_width, 3)
    if not (min_correlation <= best_corr <= max_correlation):
        report["reason"] = (
            "corridor unreachable from this source: side content too small for "
            f"correlation range {min_correlation}…{max_correlation}"
        )
    report["correlation_after"] = round(best_corr, 3)
    report["mono_loss_db"] = round(mono_loss_db(out), 2)
    report["matched"] = min_correlation <= best_corr <= max_correlation
    return out, report

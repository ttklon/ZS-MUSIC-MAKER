# -*- coding: utf-8 -*-
"""modules/dsp/limiter.py — look-ahead лимитер и мягкий клиппер.

Алгоритм (прозрачный, без «магии»):

1. огибающая пика = скользящий максимум |L|,|R| на окне look-ahead;
2. требуемое усиление `ceil / env` (в дБ — отрицательное только там, где громко);
3. сглаживание освобождения на контрольной частоте (блок ≈128 сэмплов) —
   это в 100+ раз быстрее пошагового цикла и не слышно на слух;
4. два прохода по true-peak: если после сглаживания межсэмпловый пик всё ещё
   выше потолка — домножаем весь буфер (никогда не клиппим сэмплы).

`soft_clip` — мягкое ограничение пиков выше колена (по умолчанию −6 dBFS):
именно оно, а не компрессор, позволяет громким мастерам держать −1 dBTP,
не превращая трек в кашу. Ниже колена сигнал не меняется вообще.
"""

from __future__ import annotations

import numpy as np

from modules.dsp.metrics import true_peak_dbtp

__all__ = ["CONTROL_BLOCK", "limit", "soft_clip"]

CONTROL_BLOCK = 128


def _sliding_max(values: np.ndarray, window: int) -> np.ndarray:
    """Скользящий максимум (look-ahead) без потерь на краях."""
    if window <= 1 or values.size == 0:
        return values
    try:
        from scipy.ndimage import maximum_filter1d

        return maximum_filter1d(values, size=window, mode="nearest")
    except Exception:  # pragma: no cover - scipy в зависимостях
        padded = np.pad(values, (window // 2, window - 1 - window // 2), mode="edge")
        from numpy.lib.stride_tricks import sliding_window_view

        return sliding_window_view(padded, window).max(axis=1)


def _smooth_gain(gain: np.ndarray, release_ms: float, sample_rate: int, block: int = CONTROL_BLOCK) -> np.ndarray:
    """Освобождение усиления: быстрая атака (мгновенно), плавный возврат."""
    n = gain.shape[0]
    n_blocks = max(int(np.ceil(n / block)), 1)
    pad = n_blocks * block - n
    padded = np.pad(gain, (0, pad), mode="edge") if pad else gain
    blocks = padded.reshape(n_blocks, block).min(axis=1)
    release = float(np.exp(-max(block, 1) / max(sample_rate * release_ms / 1000.0, 1.0)))
    smoothed = np.empty_like(blocks)
    state = 1.0
    for i in range(blocks.shape[0]):
        cur = float(blocks[i])
        state = cur if cur < state else release * state + (1.0 - release) * cur
        smoothed[i] = state
    centers = (np.arange(n_blocks) + 0.5) * block
    out = np.interp(np.arange(n), centers, smoothed, left=smoothed[0], right=smoothed[-1])
    return np.minimum(out, gain)


def limit(
    x: np.ndarray,
    sample_rate: int,
    *,
    ceiling_dbtp: float = -1.0,
    lookahead_ms: float = 3.0,
    release_ms: float = 60.0,
) -> tuple[np.ndarray, dict[str, float]]:
    """Ограничить буфер по true-peak. Возвращает `(out, info)`."""
    arr = np.asarray(x, dtype=np.float64)
    squeeze = arr.ndim == 1
    work = arr[:, None] if squeeze else arr
    if work.size == 0:
        return arr, {"ceiling_dbtp": ceiling_dbtp, "gain_reduction_db": 0.0}

    ceiling = float(10.0 ** (ceiling_dbtp / 20.0))
    window = max(int(sample_rate * lookahead_ms / 1000.0), 1)
    detection = _sliding_max(np.max(np.abs(work), axis=1), window)
    gain = np.minimum(1.0, ceiling / np.maximum(detection, 1e-9))
    smoothed = _smooth_gain(gain, release_ms, sample_rate)

    out = work * smoothed[:, None]
    for _ in range(2):
        tp = true_peak_dbtp(out)
        if tp <= ceiling_dbtp:
            break
        out *= float(10.0 ** ((ceiling_dbtp - tp) / 20.0))

    gr = float(-20.0 * np.log10(max(float(np.min(smoothed)), 1e-9)))
    if squeeze:
        out = out[:, 0]
    return out, {
        "ceiling_dbtp": ceiling_dbtp,
        "lookahead_ms": lookahead_ms,
        "gain_reduction_db": round(gr, 2),
        "true_peak_dbtp": round(true_peak_dbtp(out), 2),
    }


def soft_clip(x: np.ndarray, knee_dbfs: float = -6.0) -> tuple[np.ndarray, dict[str, float]]:
    """Мягко ограничить пики выше колена. Ниже колена — сигнал идентичен входу."""
    arr = np.asarray(x, dtype=np.float64)
    if arr.size == 0:
        return arr, {"knee_dbfs": knee_dbfs, "clipped_samples": 0}
    knee = float(10.0 ** (knee_dbfs / 20.0))
    magnitude = np.abs(arr)
    over = magnitude > knee
    clipped = int(np.count_nonzero(over))
    if clipped == 0:
        return arr.copy(), {"knee_dbfs": knee_dbfs, "clipped_samples": 0, "max_input_dbfs": round(20.0 * np.log10(float(magnitude.max()) + 1e-12), 2)}
    shaped = knee + (1.0 - knee) * np.tanh((magnitude - knee) / max(1.0 - knee, 1e-6))
    out = np.sign(arr) * np.where(over, shaped, magnitude)
    return out, {
        "knee_dbfs": knee_dbfs,
        "clipped_samples": clipped,
        "clipped_percent": round(100.0 * clipped / arr.size, 3),
        "max_input_dbfs": round(20.0 * np.log10(float(magnitude.max()) + 1e-12), 2),
    }

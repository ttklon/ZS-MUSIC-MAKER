# -*- coding: utf-8 -*-
"""modules/dsp/dynamics.py — компрессоры (канальный и многополосный).

Детектор считается на контрольной частоте (блок ≈128 сэмплов), а усиление
интерполируется на аудио-частоту. Это стандартный приём в компрессорах: он
даёт ту же огибающую, но в 100+ раз быстрее, чем пошаговый Python-цикл по
каждому сэмплу (на 3-минутном треке разница — минуты против секунд).

Компрессор stereo-linked: картинка не разъезжается, потому что усиление одно
на оба канала. Мягкое колено — в дБ-домене.
"""

from __future__ import annotations

import numpy as np

from modules.dsp.filters import split_bands
from modules.dsp.metrics import rms_dbfs

__all__ = ["compress", "control_envelope", "multiband_compress"]

CONTROL_BLOCK = 128


def _as_2d(x: np.ndarray) -> tuple[np.ndarray, bool]:
    arr = np.asarray(x, dtype=np.float64)
    if arr.ndim == 1:
        return arr[:, None], True
    return arr, False


def _block_level_db(work: np.ndarray, block: int) -> np.ndarray:
    """Пиковый уровень по блокам (дБ), stereo-linked."""
    n = work.shape[0]
    n_blocks = max(int(np.ceil(n / block)), 1)
    pad = n_blocks * block - n
    padded = np.pad(work, ((0, pad), (0, 0)), mode="edge") if pad else work
    peaks = np.max(np.abs(padded.reshape(n_blocks, block, work.shape[1])), axis=(1, 2))
    return 20.0 * np.log10(np.maximum(peaks, 1e-9))


def control_envelope(
    work: np.ndarray, sample_rate: int, attack_ms: float, release_ms: float, block: int = CONTROL_BLOCK
) -> np.ndarray:
    """Огибающая в дБ на контрольной частоте (длина = числу сэмплов)."""
    n = work.shape[0]
    level_db = _block_level_db(work, block)
    attack = float(np.exp(-max(block, 1) / max(sample_rate * attack_ms / 1000.0, 1.0)))
    release = float(np.exp(-max(block, 1) / max(sample_rate * release_ms / 1000.0, 1.0)))
    env = np.empty_like(level_db)
    state = float(level_db[0]) if level_db.size else -120.0
    for i in range(level_db.shape[0]):
        cur = float(level_db[i])
        coef = attack if cur > state else release
        state = coef * state + (1.0 - coef) * cur
        env[i] = state
    centers = (np.arange(env.size) + 0.5) * block
    return np.interp(np.arange(n), centers, env, left=env[0], right=env[-1])


def compress(
    x: np.ndarray,
    sample_rate: int,
    *,
    threshold_db: float = -18.0,
    ratio: float = 2.0,
    attack_ms: float = 10.0,
    release_ms: float = 120.0,
    knee_db: float = 6.0,
    makeup: bool = True,
) -> tuple[np.ndarray, dict[str, float]]:
    """Стерео-связанная компрессия. Возвращает `(out, info)` с измеренным GR."""
    work, squeeze = _as_2d(x)
    if work.size == 0 or ratio <= 1.0:
        return (work[:, 0] if squeeze else work), {"max_gain_reduction_db": 0.0}

    env_db = control_envelope(work, sample_rate, attack_ms, release_ms)
    over = env_db - threshold_db
    if knee_db > 0:
        half = max(knee_db, 1e-6) / 2.0
        ratio_eff = np.clip(1.0 + (ratio - 1.0) * (over + half) / max(knee_db, 1e-6), 1.0, ratio)
        reduction_db = np.where(over > -half, -over * (1.0 - 1.0 / ratio_eff), 0.0)
    else:
        reduction_db = np.where(over > 0.0, -over * (1.0 - 1.0 / ratio), 0.0)

    out = work * (10.0 ** (reduction_db / 20.0))[:, None]
    gr = float(abs(np.min(reduction_db)))
    if makeup and gr > 0.0:
        out = out * (10.0 ** ((gr * 0.5) / 20.0))
    if squeeze:
        out = out[:, 0]
    return out, {
        "max_gain_reduction_db": round(gr, 2),
        "threshold_db": threshold_db,
        "ratio": ratio,
        "input_rms_dbfs": round(rms_dbfs(work), 2),
        "output_rms_dbfs": round(rms_dbfs(out), 2),
    }


def multiband_compress(
    x: np.ndarray,
    sample_rate: int,
    *,
    split_hz: float = 200.0,
    low: dict[str, float] | None = None,
    high: dict[str, float] | None = None,
) -> tuple[np.ndarray, dict[str, object]]:
    """Двухполосная компрессия с точной реконструкцией (`low + high`)."""
    low_cfg: dict[str, float] = {"threshold_db": -16.0, "ratio": 2.0, "attack_ms": 20.0, "release_ms": 180.0}
    high_cfg: dict[str, float] = {"threshold_db": -20.0, "ratio": 1.6, "attack_ms": 8.0, "release_ms": 90.0}
    low_cfg.update(low or {})
    high_cfg.update(high or {})

    low_band, high_band = split_bands(x, sample_rate, split_hz)
    low_out, low_info = compress(low_band, sample_rate, **low_cfg)
    high_out, high_info = compress(high_band, sample_rate, **high_cfg)
    info: dict[str, object] = {
        "split_hz": split_hz,
        "low": low_info,
        "high": high_info,
        "max_gain_reduction_db": round(
            max(float(low_info["max_gain_reduction_db"]), float(high_info["max_gain_reduction_db"])), 2
        ),
    }
    return low_out + high_out, info

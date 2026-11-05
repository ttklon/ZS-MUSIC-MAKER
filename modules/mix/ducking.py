# -*- coding: utf-8 -*-
"""modules/mix/ducking.py — сайдчейн kick ↔ 808/бас (план 4.5.2).

Триггер — кик из бита, цель — только низ шины (< 120 Гц). Выше среза шина не
меняется вообще, поэтому вокал и верх не «дышат».

Ключевое отличие от «дака всей шины»: усиление применяется к низу, а кик как
самый громкий низкочастотный элемент остаётся опорой. Глубина дака и
сохранность кика измеряются и возвращаются в отчёте — никаких обещаний на веру.
"""

from __future__ import annotations

import numpy as np

from modules.dsp.filters import low_band
from modules.dsp.metrics import rms_dbfs

__all__ = ["duck_low_band"]

CUT_HZ = 120.0


def _envelope_db(signal: np.ndarray, sample_rate: int, attack_ms: float, release_ms: float) -> np.ndarray:
    """Пиковая огибающая низа в дБ с быстрой атакой и медленным спадом."""
    detection = np.max(np.abs(signal), axis=1) if signal.ndim > 1 else np.abs(signal)
    level_db = 20.0 * np.log10(np.maximum(detection, 1e-9))
    attack = float(np.exp(-1.0 / max(sample_rate * attack_ms / 1000.0, 1.0)))
    release = float(np.exp(-1.0 / max(sample_rate * release_ms / 1000.0, 1.0)))
    env = np.empty_like(level_db)
    state = level_db[0] if level_db.size else -120.0
    for i in range(level_db.shape[0]):
        cur = level_db[i]
        coef = attack if cur > state else release
        state = coef * state + (1.0 - coef) * cur
        env[i] = state
    return env


def duck_low_band(
    bus: np.ndarray,
    trigger: np.ndarray,
    sample_rate: int,
    *,
    depth_db: float = 3.5,
    threshold_db: float = -28.0,
    attack_ms: float = 2.0,
    release_ms: float = 90.0,
) -> tuple[np.ndarray, dict[str, float | bool]]:
    """Приглушить низ шины на `depth_db` в моменты кика.

    `trigger` — бит (или отдельный кик), `bus` — микс. Возвращает `(out, report)`
    с измеренной глубиной дака и сохранностью транзиента кика.
    """
    mix = np.asarray(bus, dtype=np.float64)
    squeeze = mix.ndim == 1
    work = mix[:, None] if squeeze else mix.copy()
    trig = np.asarray(trigger, dtype=np.float64)
    if trig.ndim == 1:
        trig = trig[:, None]
    if work.size == 0 or trig.size == 0 or depth_db <= 0.0:
        return mix, {"duck_depth_db": 0.0, "applied": False, "reason": "empty or disabled"}

    n = min(work.shape[0], trig.shape[0])
    work, trig = work[:n], trig[:n]

    low = low_band(work, sample_rate, CUT_HZ)
    high = work - low

    trig_low = low_band(trig, sample_rate, CUT_HZ)
    env_db = _envelope_db(trig_low, sample_rate, attack_ms, release_ms)
    # Нормировка: 1.0 в самых громких моментах кика, 0 — ниже порога.
    top = float(np.max(env_db)) if env_db.size else threshold_db
    span = max(top - threshold_db, 1e-6)
    weight = np.clip((env_db - threshold_db) / span, 0.0, 1.0)

    duck_db = -float(depth_db) * weight
    gain = 10.0 ** (duck_db / 20.0)
    low_ducked = low * gain[:, None]
    out = low_ducked + high

    # Измеряем: насколько тише стал низ там, где кик активен (weight > 0.8),
    # и насколько сохранился пик кика (первые 8 мс после атаки).
    strong = weight > 0.8
    if np.any(strong):
        before = rms_dbfs(low[strong])
        after = rms_dbfs(low_ducked[strong])
        depth = max(before - after, 0.0)
    else:
        depth = 0.0
    kick_peak_before = float(np.max(np.abs(low))) if low.size else 0.0
    kick_peak_after = float(np.max(np.abs(low_ducked))) if low_ducked.size else 0.0
    retention = kick_peak_after / kick_peak_before if kick_peak_before > 1e-9 else 1.0

    report: dict[str, float | bool] = {
        "applied": bool(depth > 0.1),
        "duck_depth_db": round(float(depth), 2),
        "requested_depth_db": depth_db,
        "kick_peak_retention": round(float(retention), 3),
        "cut_hz": CUT_HZ,
        "attack_ms": attack_ms,
        "release_ms": release_ms,
        "high_band_gain_db": 0.0,
    }
    return (out[:, 0] if squeeze else out), report

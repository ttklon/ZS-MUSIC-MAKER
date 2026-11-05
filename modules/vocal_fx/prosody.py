# -*- coding: utf-8 -*-
"""modules/vocal_fx/prosody.py — просодия и фразировка вокала (4.4.3).

Живой вокал после рекордера «дышит»: фразы разного уровня, паузы с шумом
дыхания, атаки на 20–40 мс мимо сетки. Ручная правка этого — часы работы.
Здесь три измеримые операции:

1. **Фразы.** Порог по огибающей (адаптивный, от медианы громких участков)
   делит дорожку на фразы; каждая получает выравнивание уровня к медиане
   фраз, ограниченное ±6 дБ — громкость не «выпрямляется в стену».
2. **Дыхание.** Паузы между фразами (не тишина в начале/конце) приглушаются
   до −24 дБ относительно медианы фраз с плавными 30 мс рампами: вдох
   слышно как деталь, а не как шум.
3. **Тайминг.** Атаки фраз притягиваются к ближайшей доле сетки (по умолчанию
   1/16) не дальше `max_shift_ms` (30 мс) — сдвиг на целое число сэмплов,
   без растяжения.

Отчёт содержит уровни фраз до/после, количество приглушённых пауз и
максимальный сдвиг. Всё детерминировано.
"""

from __future__ import annotations

from typing import Any

import numpy as np

__all__ = [
    "PHRASE_MAX_GAIN_DB",
    "detect_phrases",
    "apply_phrase_gain",
    "duck_breaths",
    "tighten_timing",
    "process_prosody",
]

PHRASE_MAX_GAIN_DB = 6.0
BREATH_ATTENUATION_DB = -24.0
RAMP_SEC = 0.030
SILENCE_FLOOR_DB = -60.0
DEFAULT_GRID = 0.0625  # 1/16 при 60 BPM-доле


def _as_2d(audio: np.ndarray) -> np.ndarray:
    data = np.asarray(audio, dtype=np.float64)
    return data[:, None] if data.ndim == 1 else data


def _mono(audio: np.ndarray) -> np.ndarray:
    data = _as_2d(audio)
    return data.mean(axis=1)


def _envelope(mono: np.ndarray, sample_rate: int, window_sec: float = 0.010) -> np.ndarray:
    window = max(1, int(window_sec * sample_rate))
    kernel = np.ones(window, dtype=np.float64) / window
    return np.sqrt(np.convolve(mono**2, kernel, mode="same") + 1e-12)


def _db(value: float) -> float:
    return float(20.0 * np.log10(max(value, 1e-12)))


def detect_phrases(
    audio: np.ndarray,
    sample_rate: int,
    min_gap_sec: float = 0.18,
    min_phrase_sec: float = 0.12,
) -> list[tuple[int, int]]:
    """Границы фраз в сэмплах: (начало, конец) по огибающей."""
    mono = _mono(audio)
    if mono.size < sample_rate * min_phrase_sec:
        return [(0, int(mono.size))]
    envelope = _envelope(mono, sample_rate)
    loud = float(np.percentile(envelope, 85))
    if loud <= 1e-7:
        return []
    threshold = max(loud * 0.06, 10.0 ** (SILENCE_FLOOR_DB / 20.0))
    active = envelope > threshold
    # «схлопываем» короткие провалы: дилатация окном min_gap
    gap = max(1, int(min_gap_sec * sample_rate))
    kernel = np.ones(gap, dtype=np.float64)
    closed = np.convolve(active.astype(np.float64), kernel, mode="same") > 0.5
    edges = np.flatnonzero(np.diff(np.concatenate([[0], closed.astype(np.int8), [0]])))
    phrases: list[tuple[int, int]] = []
    for start, stop in zip(edges[::2], edges[1::2]):
        # дилатация расширяет границы на пол-окна: возвращаем их к реальной
        # активности, иначе фраза начинается раньше, чем звук
        inner = np.flatnonzero(active[start:stop])
        if inner.size == 0:
            continue
        start, stop = start + int(inner[0]), start + int(inner[-1]) + 1
        if (stop - start) / sample_rate >= min_phrase_sec:
            phrases.append((int(start), int(stop)))
    return phrases


def apply_phrase_gain(
    audio: np.ndarray,
    sample_rate: int,
    target_dbfs: float | None = None,
    max_gain_db: float = PHRASE_MAX_GAIN_DB,
) -> tuple[np.ndarray, list[dict[str, float]]]:
    """Выровнять уровень фраз к медиане, не более ±`max_gain_db`."""
    data = np.array(_as_2d(audio), dtype=np.float64, copy=True)
    phrases = detect_phrases(data, sample_rate)
    if not phrases:
        return data, []
    levels = []
    for start, stop in phrases:
        levels.append(_db(float(np.sqrt(np.mean(data[start:stop] ** 2)) + 1e-12)))
    target = float(target_dbfs) if target_dbfs is not None else float(np.median(levels))
    ramp = max(1, int(0.010 * sample_rate))
    fade = np.hanning(2 * ramp)[:ramp]
    report = []
    for (start, stop), level in zip(phrases, levels):
        gain_db = float(np.clip(target - level, -max_gain_db, max_gain_db))
        gain = 10.0 ** (gain_db / 20.0)
        curve = np.full(stop - start, gain)
        if curve.size > 2 * ramp:
            curve[:ramp] = 1.0 + (gain - 1.0) * fade
            curve[-ramp:] = gain + (1.0 - gain) * fade[::-1]
        data[start:stop] *= curve[:, None]
        report.append(
            {
                "start_sec": round(start / sample_rate, 3),
                "end_sec": round(stop / sample_rate, 3),
                "level_dbfs": round(level, 2),
                "gain_db": round(gain_db, 2),
            }
        )
    return data, report


def duck_breaths(
    audio: np.ndarray,
    sample_rate: int,
    attenuation_db: float = BREATH_ATTENUATION_DB,
    ramp_sec: float = RAMP_SEC,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Приглушить паузы между фразами (дыхание остаётся, шум уходит)."""
    data = np.array(_as_2d(audio), dtype=np.float64, copy=True)
    phrases = detect_phrases(data, sample_rate)
    if len(phrases) < 2:
        return data, {"pauses": 0, "attenuation_db": attenuation_db, "changed": False}
    target = 10.0 ** (float(attenuation_db) / 20.0)
    ramp = max(1, int(ramp_sec * sample_rate))
    fade = np.hanning(2 * ramp)[:ramp]
    pauses = 0
    for (_, stop), (start, _) in zip(phrases[:-1], phrases[1:]):
        if start - stop <= ramp * 2 + 16:
            continue
        gap = np.full(start - stop, target)
        gap[:ramp] = 1.0 + (target - 1.0) * fade
        gap[-ramp:] = target + (1.0 - target) * fade[::-1]
        data[stop:start] *= gap[:, None]
        pauses += 1
    return data, {
        "pauses": pauses,
        "attenuation_db": round(float(attenuation_db), 2),
        "changed": pauses > 0,
    }


def tighten_timing(
    audio: np.ndarray,
    sample_rate: int,
    bpm: float = 120.0,
    grid: float = DEFAULT_GRID,
    max_shift_ms: float = 30.0,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Притянуть атаки фраз к сетке в пределах `max_shift_ms`."""
    data = _as_2d(audio)
    phrases = detect_phrases(data, sample_rate)
    if not phrases or bpm <= 0:
        return np.array(data, copy=True), {"shifts": 0, "max_shift_ms": 0.0}
    beat = 60.0 / float(bpm)
    step = max(1e-3, beat * float(grid))
    max_shift = int(float(max_shift_ms) / 1000.0 * sample_rate)
    shifts: list[int] = []
    pieces: list[np.ndarray] = []
    cursor = 0
    for start, stop in phrases:
        position = start / sample_rate
        nearest = round(position / step) * step
        shift = int(round((nearest - position) * sample_rate))
        shift = int(np.clip(shift, -max_shift, max_shift))
        new_start = max(cursor, start + shift)
        if new_start > cursor:
            pieces.append(data[cursor:new_start])
        pieces.append(data[start:stop])
        cursor = stop
        shifts.append(abs(shift))
    pieces.append(data[cursor:])
    out = np.concatenate(pieces, axis=0)
    # обрезка/паддинг до исходной длины, чтобы стадия микса не меняла таймлайн
    if out.shape[0] < data.shape[0]:
        out = np.concatenate([out, np.zeros((data.shape[0] - out.shape[0], data.shape[1]))], axis=0)
    out = out[: data.shape[0]]
    return out, {
        "shifts": int(sum(1 for value in shifts if value > 0)),
        "max_shift_ms": round(float(max(shifts, default=0)) / sample_rate * 1000.0, 1),
        "grid_sec": round(step, 4),
    }


def process_prosody(
    audio: np.ndarray,
    sample_rate: int,
    bpm: float | None = None,
    max_gain_db: float = PHRASE_MAX_GAIN_DB,
    tighten: bool = True,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Полная просодическая цепочка: фразы → дыхание → тайминг."""
    original_ndim = np.asarray(audio).ndim
    work, phrase_report = apply_phrase_gain(audio, sample_rate, max_gain_db=max_gain_db)
    work, breath_report = duck_breaths(work, sample_rate)
    timing_report: dict[str, Any] = {"shifts": 0, "max_shift_ms": 0.0}
    if tighten and bpm:
        work, timing_report = tighten_timing(work, sample_rate, bpm=bpm)
    report = {
        "engine": "phrase_prosody",
        "phrases": phrase_report,
        "phrase_count": len(phrase_report),
        "max_gain_db": round(float(max_gain_db), 2),
        "gain_range_db": round(
            float(max((abs(item["gain_db"]) for item in phrase_report), default=0.0)), 2
        ),
        "breaths": breath_report,
        "timing": timing_report,
        "length_preserved": bool(work.shape[0] == _as_2d(audio).shape[0]),
    }
    if original_ndim == 1:
        work = np.asarray(work)[:, 0]
    return work, report

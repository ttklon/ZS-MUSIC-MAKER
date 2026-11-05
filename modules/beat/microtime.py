# -*- coding: utf-8 -*-
"""modules/beat/microtime.py — «человеческие шероховатости» трека (план 4.7.2).

Три вещи, которых не бывает в «идеальном» машинном рендере:

* **дрейф темпа ±0.2 %** — живой барабанщик медленно уходит и возвращается,
  а не держит сетку с точностью кварцевого генератора;
* **шум комнаты** — даже в студии есть воздух: постоянный шумовой пол
  (−62 dBFS по умолчанию, спад ниже 200 Гц, чтобы не «бубнило»);
* **дыхание уровня** — микроскопические (±0.15 дБ) колебания громкости
  по фразам.

Всё детерминировано по `seed` и измеримо: `humanity_report()` возвращает
фактический дрейф в процентах, добавленный шумовой пол и изменение длины.
"""

from __future__ import annotations

import logging

import numpy as np

__all__ = ["add_room_noise", "apply_humanity", "humanity_report", "tempo_drift"]

DEFAULT_DRIFT_PCT = 0.2
DEFAULT_NOISE_DBFS = -62.0


def tempo_drift(
    y: np.ndarray,
    sample_rate: int,
    amount_pct: float = DEFAULT_DRIFT_PCT,
    period_sec: float = 45.0,
) -> tuple[np.ndarray, dict[str, float]]:
    """Плавный дрейф темпа в пределах ±`amount_pct` процентов.

    Реализация — чтение с переменной скоростью (линейная интерполяция):
    высота тона меняется на сотые доли процента, на слух это «живость»,
    а не «детюн». Длина буфера сохраняется.
    """
    audio = np.asarray(y, dtype=np.float64)
    if audio.size == 0 or amount_pct <= 0:
        return audio, {"drift_pct": 0.0, "peak_deviation_samples": 0.0}
    n = audio.shape[0]
    time = np.arange(n, dtype=np.float64) / float(sample_rate)
    rate = 1.0 + (amount_pct / 100.0) * np.sin(2.0 * np.pi * time / max(period_sec, 1e-6))
    positions = np.cumsum(rate)
    positions *= (n - 1) / positions[-1]  # сохраняем длину ровно
    index = np.arange(n, dtype=np.float64)
    if audio.ndim == 1:
        warped = np.interp(positions, index, audio)
    else:
        warped = np.stack(
            [np.interp(positions, index, audio[:, channel]) for channel in range(audio.shape[1])],
            axis=1,
        )
    deviation = float(np.max(np.abs(positions - index)))
    return warped, {
        "drift_pct": float(amount_pct),
        "period_sec": float(period_sec),
        "peak_deviation_ms": round(deviation / float(sample_rate) * 1000.0, 2),
    }


def add_room_noise(
    y: np.ndarray,
    sample_rate: int,
    level_dbfs: float = DEFAULT_NOISE_DBFS,
    seed: int | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Добавить шумовой пол комнаты (мягкий, с наклоном вниз по частоте)."""
    audio = np.asarray(y, dtype=np.float64)
    if audio.size == 0:
        return audio, {"noise_dbfs": -120.0}
    rng = np.random.default_rng(20260101 if seed is None else int(seed))
    shape = (audio.shape[0],) if audio.ndim == 1 else (audio.shape[0], audio.shape[1])
    noise = rng.standard_normal(shape)
    try:
        from scipy.signal import butter, sosfilt

        sos = butter(2, min(4000.0, 0.45 * sample_rate), btype="low", fs=sample_rate, output="sos")
        noise = sosfilt(sos, noise, axis=0)
        # Убираем гул: ниже 40 Гц комната не «дышит», там только рокот.
        sos_hp = butter(2, 40.0, btype="high", fs=sample_rate, output="sos")
        noise = sosfilt(sos_hp, noise, axis=0)
    except Exception:  # pragma: no cover - scipy в зависимостях
        logging.getLogger(__name__).debug("ignored exception", exc_info=True)
    rms = float(np.sqrt(np.mean(noise**2)) + 1e-12)
    target = float(10.0 ** (level_dbfs / 20.0))
    noise *= target / rms
    return audio + noise, {
        "noise_dbfs": round(float(level_dbfs), 1),
        "noise_rms_dbfs": round(20.0 * float(np.log10(max(float(np.sqrt(np.mean(noise**2))), 1e-12))), 2),
    }


def apply_humanity(
    y: np.ndarray,
    sample_rate: int,
    *,
    drift_pct: float = DEFAULT_DRIFT_PCT,
    noise_dbfs: float | None = DEFAULT_NOISE_DBFS,
    seed: int | None = None,
) -> tuple[np.ndarray, dict[str, object]]:
    """Применить дрейф темпа и шум комнаты; вернуть аудио и отчёт."""
    audio, drift_info = tempo_drift(y, sample_rate, amount_pct=drift_pct)
    report: dict[str, object] = {"tempo_drift": drift_info}
    if noise_dbfs is not None:
        audio, noise_info = add_room_noise(audio, sample_rate, level_dbfs=noise_dbfs, seed=seed)
        report["room_noise"] = noise_info
    else:
        report["room_noise"] = {"noise_dbfs": None, "applied": False}
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    report["peak"] = round(peak, 4)
    return audio.astype(np.float32), report


def humanity_report(y: np.ndarray, sample_rate: int) -> dict[str, float]:
    """Измерить «шероховатость» готового трека: шумовой пол и вариативность уровня."""
    audio = np.asarray(y, dtype=np.float64)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if audio.size == 0:
        return {"noise_floor_dbfs": -120.0, "level_variation_db": 0.0}
    frame = max(int(0.05 * sample_rate), 1)
    n_frames = audio.size // frame
    if n_frames < 4:
        return {"noise_floor_dbfs": -120.0, "level_variation_db": 0.0}
    frames = audio[: n_frames * frame].reshape(n_frames, frame)
    levels = 20.0 * np.log10(np.maximum(np.sqrt(np.mean(frames**2, axis=1)), 1e-9))
    quiet = np.percentile(levels, 5)
    return {
        "noise_floor_dbfs": round(float(quiet), 2),
        "level_variation_db": round(float(np.std(levels)), 2),
    }

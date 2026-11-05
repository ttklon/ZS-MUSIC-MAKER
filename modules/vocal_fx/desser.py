# -*- coding: utf-8 -*-
"""modules/vocal_fx/desser.py — динамический де-эссер (4.4.2).

Статический срез полосы 4.5–9.5 кГц глушит «воздух» даже там, где сибилянтов
нет. Здесь — управляемое усиление только в моменты шипящих:

1. полосовой фильтр 4.5–9.5 кГц (баттерворт 4-го порядка);
2. огибающая полосы с атакой 1 мс и спадом 40 мс;
3. если огибающая выше порога — коэффициент усиления полосы падает до
   `10^(−reduction/20)`, максимум `max_reduction_db` (по умолчанию 6 дБ);
4. полоса возвращается в сигнал (сумма с низкочастотной частью), поэтому
   выше 10 кГц спектр не меняется вовсе.

Вектор операций, без циклов по сэмплам; детерминированно.
"""

from __future__ import annotations

from typing import Any

import numpy as np

__all__ = [
    "DEESSER_LOW_HZ",
    "DEESSER_HIGH_HZ",
    "RATIO_THRESHOLD",
    "dynamic_deess",
    "sibilance_energy",
]

DEESSER_LOW_HZ = 4500.0
DEESSER_HIGH_HZ = 9500.0
ATTACK_SEC = 0.001
RELEASE_SEC = 0.040
DEFAULT_THRESHOLD_DB = -34.0
DEFAULT_REDUCTION_DB = 6.0
RATIO_THRESHOLD = 0.30


def _as_2d(audio: np.ndarray) -> np.ndarray:
    data = np.asarray(audio, dtype=np.float64)
    if data.ndim == 1:
        return data[:, None]
    return data


def _band(audio: np.ndarray, sample_rate: int, low: float, high: float) -> np.ndarray:
    """Идеальная (нулевая фаза) полоса по FFT с косинусными переходами.

    Баттерворт сдвигает фазу, поэтому `data − bandpass(data)` не является
    «остатком»: после обратного вычитания полосы в сигнал возвращается
    фазоискажённая копия, и де-эссер почти не слышен. Нулевая фаза делает
    вычитание точным (полосы дополняют друг друга до семпла).
    """
    data = np.asarray(audio, dtype=np.float64)
    mono = data if data.ndim == 2 else data[:, None]
    size = mono.shape[0]
    if size < 16:
        return np.zeros_like(mono)
    freqs = np.fft.rfftfreq(size, 1.0 / sample_rate)
    nyquist = sample_rate / 2.0
    high = min(high, nyquist * 0.98)
    low = max(low, 0.0)
    taper = max(1.0, 0.15 * (high - low))
    mask = np.zeros_like(freqs)
    rising = (freqs >= low) & (freqs < low + taper)
    mask[rising] = 0.5 - 0.5 * np.cos(np.pi * (freqs[rising] - low) / taper)
    mask[(freqs >= low + taper) & (freqs <= high - taper)] = 1.0
    falling = (freqs > high - taper) & (freqs <= high)
    mask[falling] = 0.5 + 0.5 * np.cos(np.pi * (freqs[falling] - (high - taper)) / taper)
    spectrum = np.fft.rfft(mono, axis=0) * mask[:, None]
    result = np.fft.irfft(spectrum, size, axis=0)
    return result if data.ndim == 2 else result[:, 0]


def _envelope(signal: np.ndarray, sample_rate: int) -> np.ndarray:
    """Огибающая по модулю: быстрый однополюсник плюс медленный (векторно).

    Максимум двух сглаживаний даёт «атака 1 мс, спад 40 мс» без циклов по
    сэмплам: медленный фильтр держит пик на спаде, быстрый ловит фронт.
    """
    from scipy.signal import lfilter

    rectified = np.max(np.abs(signal), axis=1)
    attack = 1.0 - np.exp(-1.0 / max(1.0, ATTACK_SEC * sample_rate))
    release = 1.0 - np.exp(-1.0 / max(1.0, RELEASE_SEC * sample_rate))
    fast = lfilter([attack], [1.0, attack - 1.0], rectified)
    slow = lfilter([release], [1.0, release - 1.0], rectified)
    return np.maximum(fast, slow)


def sibilance_energy(audio: np.ndarray, sample_rate: int) -> float:
    """Энергия полосы сибилянтов (дБFS) — одна метрика до/после."""
    band = _band(_as_2d(audio), sample_rate, DEESSER_LOW_HZ, DEESSER_HIGH_HZ)
    rms = float(np.sqrt(np.mean(band**2)) + 1e-12)
    return round(20.0 * np.log10(rms), 2)


def dynamic_deess(
    audio: np.ndarray,
    sample_rate: int,
    threshold_db: float | None = None,
    reduction_db: float = DEFAULT_REDUCTION_DB,
    ratio_threshold: float = RATIO_THRESHOLD,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Подавить сибилянты адаптивно и вернуть отчёт.

    Ключ к «как у людей»: де-эссер реагирует не на абсолютный уровень полосы,
    а на её **долю в общем сигнале**. Сибилянт — это когда 4.5–9.5 кГц дают
    заметную часть энергии; гласная с гармоникой в этой полосе — нет.
    Поэтому `ratio = env_band / env_full`:

    * `ratio ≤ ratio_threshold` (0.30) — полоса не трогается вообще;
    * `ratio > ratio_threshold` — подавление растёт линейно и упирается в
      `reduction_db` (по умолчанию 6 дБ);
    * тишина ниже −70 dBFS игнорируется (иначе шум паузы считался бы
      сибилянтом).

    `threshold_db` можно задать вручную — тогда работает только абсолютный
    порог (для отладки/совместимости), и режим честно пишется в отчёт.
    """
    data = _as_2d(audio)
    band = _band(data, sample_rate, DEESSER_LOW_HZ, DEESSER_HIGH_HZ)
    low = data - band
    band_env = _envelope(band, sample_rate)
    full_env = _envelope(data, sample_rate)
    band_db = 20.0 * np.log10(np.maximum(band_env, 1e-9))
    ratio = band_env / np.maximum(full_env, 1e-9)
    if threshold_db is None:
        threshold = float(np.percentile(band_db[band_db > -120.0], 60)) + 2.0 if np.any(band_db > -120.0) else DEFAULT_THRESHOLD_DB
        mode = "ratio_adaptive"
        excess = np.clip(ratio / max(ratio_threshold, 1e-3) - 1.0, 0.0, 1e3)
        reduction = np.minimum(excess * 6.0, float(reduction_db))
    else:
        threshold = float(threshold_db)
        mode = "manual_absolute"
        excess = np.clip(band_db - threshold, 0.0, 2.0 * float(reduction_db))
        reduction = np.minimum(excess, float(reduction_db))
    # тишина не де-эссится: ниже −70 dBFS сигнала в полосе практически нет
    reduction = np.where(band_db > -70.0, reduction, 0.0)
    gain = np.clip(10.0 ** (-reduction / 20.0), 10.0 ** (-float(reduction_db) / 20.0), 1.0)
    smooth = max(1, min(max(3, int(0.0015 * sample_rate)), gain.size))
    # np.convolve("same") на коротком буфере вернул бы длину ядра — режем обратно
    smoothed = np.convolve(gain, np.ones(smooth) / smooth, mode="same")[: gain.size]
    smoothed = np.minimum(smoothed, gain)  # на фронте не пропускаем пик
    output = low + band * smoothed[:, None]
    report = {
        "engine": "dynamic_band_deesser",
        "band_hz": [DEESSER_LOW_HZ, DEESSER_HIGH_HZ],
        "threshold_db": round(float(threshold), 2),
        "threshold_mode": mode,
        "ratio_threshold": round(float(ratio_threshold), 3),
        "max_reduction_db": round(float(reduction_db), 2),
        "ratio_median": round(float(np.median(ratio)), 3),
        "ratio_p95": round(float(np.percentile(ratio, 95)), 3),
        "gain_reduction_db_median": round(float(np.median(reduction)), 2),
        "gain_reduction_db_p95": round(float(np.percentile(reduction, 95)), 2),
        "reduction_active_pct": round(float(np.mean(reduction > 0.05) * 100.0), 1),
        "sibilance_before_dbfs": sibilance_energy(data, sample_rate),
        "sibilance_after_dbfs": sibilance_energy(output, sample_rate),
        "sibilance_reduction_db": round(
            sibilance_energy(data, sample_rate) - sibilance_energy(output, sample_rate), 2
        ),
        "length_preserved": bool(output.shape[0] == data.shape[0]),
    }
    return output, report

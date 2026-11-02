# -*- coding: utf-8 -*-
"""modules/dsp/metrics.py — единственная точка измерения аудио-уровней.

Что измеряется (всё объективно, без «на слух»):

* **RMS / peak / crest** — уровень и динамика (дБ).
* **true peak** — 4× передискретизация (ITU-R BS.1770 аппроксимация межсэмпловых пиков).
* **LUFS** — интегрированная громкость через pyloudnorm; если его нет, честная
  оценка `RMS_dBFS − 3 дБ` с явным статусом `dbfs_estimate` (никогда не выдаётся
  за настоящий LUFS).
* **stereo correlation / side-to-mid / mono loss** — проверка ширины и моно-совместимости.

Все функции принимают `(N,)` или `(N, C)` и никогда не падают на тишине:
на пустом/тихом буфере возвращаются конечные значения (`-120 дБ`, корреляция 1.0).
"""

from __future__ import annotations

import numpy as np

_EPS = 1e-12
_FLOOR_DB = -120.0

__all__ = [
    "MONO_FLOOR_DB",
    "active_window",
    "as_2d",
    "clipping_samples",
    "crest_db",
    "integrated_lufs",
    "loudness_report",
    "mono_loss_db",
    "peak_dbfs",
    "reference_crest_db",
    "reference_rms_dbfs",
    "rms_dbfs",
    "stereo_correlation",
    "true_peak_dbtp",
]

MONO_FLOOR_DB = _FLOOR_DB


def as_2d(y: np.ndarray) -> np.ndarray:
    """Привести буфер к форме (N, C) float64 без копирования, если уже 2D."""
    arr = np.asarray(y, dtype=np.float64)
    if arr.ndim == 1:
        return arr[:, None]
    if arr.ndim != 2:
        raise ValueError(f"expected 1D/2D audio, got shape {arr.shape}")
    return arr


def _db(x: float) -> float:
    return float(20.0 * np.log10(max(float(x), _EPS)))


def rms_dbfs(y: np.ndarray) -> float:
    """RMS всего буфера в dBFS (тишина → −120 дБ, а не −inf)."""
    arr = np.asarray(y, dtype=np.float64)
    if arr.size == 0:
        return _FLOOR_DB
    return max(_db(float(np.sqrt(np.mean(arr**2)))), _FLOOR_DB)


def peak_dbfs(y: np.ndarray) -> float:
    """Сэмпловый пик в dBFS."""
    arr = np.asarray(y, dtype=np.float64)
    if arr.size == 0:
        return _FLOOR_DB
    return max(_db(float(np.max(np.abs(arr)))), _FLOOR_DB)


def true_peak_dbtp(y: np.ndarray, oversample: int = 4) -> float:
    """True peak (dBTP): 4× передискретизация всего буфера, потоково.

    Раньше передискретизировались только 48 самых громких участков по
    сэмпловому пику. На клиппированном материале все пики равны по амплитуде,
    а межсэмпловый перегруз гуляет от участка к участку: метод видел −1.0 dBTP
    там, где честное 4× давало +0.4 dBTP, и лимитер из-за этого «прятался» на
    несколько дБ ниже потолка (мастера выходили тише на 3–4 дБ, а громкость
    добивалась клиппингом). Теперь буфер режется на окна по 10 с с запасом:
    внутри окна результат совпадает с полным расчётом до 0.01 дБ, память —
    мегабайты, а не гигабайты.
    """
    arr = as_2d(y)
    if arr.size == 0:
        return _FLOOR_DB
    sample_peak = float(np.max(np.abs(arr)))
    if oversample <= 1 or sample_peak < 1e-9:
        return max(_db(sample_peak), _FLOOR_DB)
    try:
        from scipy.signal import resample_poly
    except Exception:  # pragma: no cover - scipy в зависимостях
        return max(_db(sample_peak), _FLOOR_DB)

    margin = 256  # больше половины FIR-ядра (10·up сэмплов)
    window = 441_000
    best = sample_peak
    for start in range(0, arr.shape[0], window):
        stop = min(start + window, arr.shape[0])
        lo = max(0, start - margin)
        hi = min(arr.shape[0], stop + margin)
        chunk = arr[lo:hi]
        if chunk.shape[0] < 8:
            continue
        upsampled = resample_poly(chunk, oversample, 1, axis=0)
        lead = (start - lo) * oversample
        tail = upsampled.shape[0] - (hi - stop) * oversample
        interior = upsampled[lead:tail]
        if interior.size == 0:
            continue
        best = max(best, float(np.max(np.abs(interior))))
    return max(_db(best), _FLOOR_DB)


def crest_db(y: np.ndarray) -> float:
    """Crest factor: peak − RMS (дБ). Для микса норма 8…14 дБ."""
    arr = np.asarray(y, dtype=np.float64)
    if arr.size == 0:
        return 0.0
    peak = float(np.max(np.abs(arr)))
    rms = float(np.sqrt(np.mean(arr**2)))
    if rms < _EPS:
        return 0.0
    return float(_db(peak) - _db(rms))


def active_window(y: np.ndarray, sample_rate: int, window_sec: float = 10.0) -> np.ndarray:
    """Вернуть самый громкий участок длиной `window_sec` (по энергии).

    Гейты уровня/креста измеряются по нему, а не по всему треку: иначе тихий
    интро-проигрыш «делает» микс тише нормы, хотя громкая часть сведена верно.
    """
    arr = np.asarray(y, dtype=np.float64)
    if arr.size == 0 or sample_rate <= 0:
        return arr
    n = min(int(window_sec * sample_rate), arr.shape[0])
    if n <= 0 or n >= arr.shape[0]:
        return arr
    power = np.sum(arr**2, axis=1) if arr.ndim == 2 else arr**2
    csum = np.concatenate([[0.0], np.cumsum(power)])
    means = (csum[n:] - csum[:-n]) / n
    start = int(np.argmax(means))
    return arr[start : start + n]


def reference_rms_dbfs(y: np.ndarray, sample_rate: int, window_sec: float = 10.0) -> float:
    """RMS самого громкого участка — «опорный уровень» микса."""
    return rms_dbfs(active_window(y, sample_rate, window_sec))


def reference_crest_db(y: np.ndarray, sample_rate: int, window_sec: float = 10.0) -> float:
    """Crest factor самого громкого участка (норма микса 8…14 дБ)."""
    return crest_db(active_window(y, sample_rate, window_sec))


def stereo_correlation(y: np.ndarray) -> float:
    """Нормированная корреляция L/R. Моно/тишина → 1.0, антифаза → −1.0."""
    arr = as_2d(y)
    if arr.shape[1] < 2:
        return 1.0
    left, right = arr[:, 0], arr[:, 1]
    denom = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denom < _EPS:
        return 1.0
    return float(np.clip(float(np.dot(left, right) / denom), -1.0, 1.0))


def mono_loss_db(y: np.ndarray) -> float:
    """Сколько дБ теряет трек при сворачивании в моно (0 = без потерь)."""
    arr = as_2d(y)
    if arr.shape[1] < 2 or arr.size == 0:
        return 0.0
    stereo_rms = float(np.sqrt(np.mean(arr**2)))
    mono_rms = float(np.sqrt(np.mean(((arr[:, 0] + arr[:, 1]) * 0.5) ** 2)))
    if stereo_rms < _EPS:
        return 0.0
    return float(_db(stereo_rms) - _db(mono_rms))


def integrated_lufs(y: np.ndarray, sample_rate: int) -> tuple[float, dict[str, str]]:
    """Интегрированная громкость LUFS + честная мета-информация об источнике.

    Возвращает `(value, info)`, где `info["lufs_engine"]` — `pyloudnorm` или
    `dbfs_estimate`, а `info["lufs_status"]` — `ok` / `unavailable` / `failed`.
    """
    arr = as_2d(y)
    fallback = max(rms_dbfs(arr) - 3.0, _FLOOR_DB)
    if arr.size == 0:
        return fallback, {"lufs_engine": "dbfs_estimate", "lufs_status": "empty"}
    try:
        import pyloudnorm as pyln  # type: ignore
    except Exception:  # pragma: no cover - зависит от окружения
        return fallback, {"lufs_engine": "dbfs_estimate", "lufs_status": "unavailable"}
    try:
        meter = pyln.Meter(int(sample_rate))
        # BS.1770 суммирует энергию каналов: сводить в моно нельзя — это
        # систематически занижает LUFS на ~3 дБ и «ломает» целевые стенды.
        value = float(meter.integrated_loudness(arr if arr.shape[1] > 1 else arr[:, 0]))
        if not np.isfinite(value):
            raise ValueError("pyloudnorm returned non-finite loudness")
        return value, {"lufs_engine": "pyloudnorm", "lufs_status": "ok"}
    except Exception as exc:  # pragma: no cover - путь деградации
        return fallback, {
            "lufs_engine": "dbfs_estimate",
            "lufs_status": "failed",
            "lufs_error": f"{type(exc).__name__}: {exc}",
        }


def clipping_samples(y: np.ndarray, ceiling: float = 0.999) -> int:
    """Сколько сэмплов достигло потолка (истинный клиппинг, а не «громко»)."""
    arr = np.asarray(y, dtype=np.float64)
    if arr.size == 0:
        return 0
    return int(np.count_nonzero(np.abs(arr) >= ceiling))


def loudness_report(y: np.ndarray, sample_rate: int) -> dict[str, float | str | int]:
    """Полный паспорт уровня/стерео для одного буфера — основа всех гейтов."""
    arr = as_2d(y)
    lufs, info = integrated_lufs(arr, sample_rate)
    report: dict[str, float | str | int] = {
        "sample_rate": int(sample_rate),
        "channels": int(arr.shape[1]),
        "duration_sec": round(arr.shape[0] / float(sample_rate), 3) if sample_rate else 0.0,
        "rms_dbfs": round(rms_dbfs(arr), 2),
        "peak_dbfs": round(peak_dbfs(arr), 2),
        "true_peak_dbtp": round(true_peak_dbtp(arr), 2),
        "crest_db": round(crest_db(arr), 2),
        "lufs": round(float(lufs), 2),
        "stereo_correlation": round(stereo_correlation(arr), 3),
        "mono_loss_db": round(mono_loss_db(arr), 2),
        "clipping_samples": clipping_samples(arr),
        **info,
    }
    return report

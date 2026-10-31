# -*- coding: utf-8 -*-
"""
modules/vocal_fx/dsp.py — низкоуровневые DSP-примитивы вокальных эффектов.

Только numpy + soundfile, никаких нейросетей. Все функции честные: если
бэкенда нет, `_OK=False`, а вызывающий код обязан вернуть отказ с причиной.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

try:
    import numpy as _np
    import soundfile as _sf

    _OK = True
except Exception:
    _np = None
    _sf = None
    _OK = False


def _read(wav_path: str) -> tuple[Any, int]:
    y, sr = _sf.read(wav_path, always_2d=True)
    return y.astype("float32"), int(sr)


def _write(wav_path: str, y, sr: int) -> str:
    Path(wav_path).parent.mkdir(parents=True, exist_ok=True)
    _sf.write(wav_path, _np.clip(y, -1.0, 1.0), sr)
    return wav_path


def _resample_linear(y, factor: float):
    """Честный линейный ресемпл по времени (без scipy).

    factor > 1 — сигнал короче/выше; < 1 — длиннее/ниже.
    Используется для микро-растяжения дабла (0.994–1.006), где
    линейная интерполяция не даёт слышимых артефактов.
    """
    n = len(y)
    if n < 2:
        return y
    new_n = max(2, int(round(n / factor)))
    x_old = _np.linspace(0.0, 1.0, n)
    x_new = _np.linspace(0.0, 1.0, new_n)
    if y.ndim == 1:
        return _np.interp(x_new, x_old, y).astype("float32")
    out = _np.empty((new_n, y.shape[1]), dtype="float32")
    for c in range(y.shape[1]):
        out[:, c] = _np.interp(x_new, x_old, y[:, c])
    return out


def _detune_cents(y, sr: int, cents: float):
    """Детюн в центах через ресемпл (честный pitch+time shift)."""
    factor = 2.0 ** (cents / 1200.0)
    return _resample_linear(y, factor)


def _fit_len(y, n: int):
    if len(y) == n:
        return y
    if len(y) > n:
        return y[:n]
    pad = _np.zeros((n - len(y),) + y.shape[1:], dtype=y.dtype)
    return _np.concatenate([y, pad], axis=0)


def _rms_db(x) -> float:
    r = float(_np.sqrt(_np.mean(x**2)) + 1e-9)
    return 20.0 * math.log10(r)


def _find_phrase_ends(
    mono, sr: int, silence_db: float = -40.0, min_silence_ms: int = 180
) -> list[int]:
    """Грубый VAD: ищем концы фраз = начало длинной паузы.

    Возвращает список sample-индексов, где фраза заканчивается
    (за ними идёт тишина). На них вешаем delay throw.
    """
    frame = max(1, int(sr * 0.02))  # 20 ms окно
    hop = frame
    n_fr = max(1, len(mono) // hop)
    rms = _np.empty(n_fr, dtype="float32")
    for i in range(n_fr):
        seg = mono[i * hop : (i + 1) * hop]
        rms[i] = float(_np.sqrt(_np.mean(seg**2)) + 1e-9)
    thr = 10.0 ** (silence_db / 20.0)
    voiced = rms > thr
    min_sil_frames = max(1, int(min_silence_ms / 20.0))
    ends: list[int] = []
    i = 0
    while i < n_fr:
        if voiced[i]:
            # ищем конец voiced-участка
            j = i
            while j < n_fr and voiced[j]:
                j += 1
            # j — первый тихий фрейм; если тишина длинная — это конец фразы
            k = j
            while k < n_fr and not voiced[k]:
                k += 1
            if (k - j) >= min_sil_frames and j > 0:
                ends.append(j * hop)
            i = k
        else:
            i += 1
    return ends

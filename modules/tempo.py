"""Разбор темпа из librosa в скаляр.

`librosa.beat.beat_track` с 0.11 возвращает tempo массивом формы (1,), а не
числом: `float(tempo)` на нём падает `TypeError: only 0-dimensional arrays can
be converted to Python scalars`. Требование `librosa>=0.10.2` такие версии
допускает, поэтому разбор темпа живёт в одном месте и покрыт тестом.
"""

from __future__ import annotations

import numpy as np


def tempo_scalar(tempo: object, default: float = 0.0) -> float:
    """Первое значение темпа как float; пустой или нечисловой вход → default."""
    try:
        arr = np.asarray(tempo, dtype=float).reshape(-1)
    except (TypeError, ValueError):
        return default
    if arr.size == 0 or not np.isfinite(arr[0]):
        return default
    return float(arr[0])

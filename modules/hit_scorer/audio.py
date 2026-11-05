# -*- coding: utf-8 -*-
"""
modules/hit_scorer/audio.py — декодирование и кэш чтения аудио.

Единственное место в пакете, где импортируются тяжёлые аудио-зависимости
(`numpy`, `librosa`, `soundfile`, `pyloudnorm`). Все они опциональны: при их
отсутствии модуль честно выставляет `HAS_* = False`, а метрики деградируют,
не падая.
"""

from __future__ import annotations

from functools import lru_cache

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None

try:
    import librosa

    HAS_LIBROSA = True
except Exception:  # pragma: no cover
    librosa = None
    HAS_LIBROSA = False

try:
    import soundfile as sf

    HAS_SF = True
except Exception:  # pragma: no cover
    sf = None
    HAS_SF = False

try:
    import pyloudnorm as pyln

    HAS_PYLOUDNORM = True
except ImportError:  # pragma: no cover
    pyln = None
    HAS_PYLOUDNORM = False


# ============================================================ utils
def _load_audio(path: str, sr: int = 22050):
    """Возвращает (y, sr). Использует librosa если есть, иначе soundfile+resample naive."""
    if HAS_LIBROSA:
        y, s = librosa.load(path, sr=sr, mono=True)
        return y, s
    if HAS_SF:
        y, s = sf.read(path, always_2d=False)
        if hasattr(y, "ndim") and y.ndim > 1:
            y = y.mean(axis=1)
        return y, s
    raise RuntimeError("Neither librosa nor soundfile available")


@lru_cache(maxsize=8)
def _load_audio_cached(path: str, sr: int, mtime_ns: int):
    """Кэшировать decode/resample только пока source file не изменился."""
    del mtime_ns
    return _load_audio(path, sr=sr)

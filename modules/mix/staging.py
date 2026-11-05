# -*- coding: utf-8 -*-
"""modules/mix/staging.py — gain staging шины (план 4.5.1).

Правило: опорный (самый громкий) участок трека сводится к −18 dBFS RMS с
запасом по пику −3 dBFS. Именно так сводят живые инженеры: гейт ставится по
громкой части, а тихое интро не делает микс «тише нормы».

Это единственное место, где считается усиление шины, поэтому «двойного» gain
нигде не бывает. Деградация не скрывается: если пик упирается в потолок
раньше уровня — `limited_by_peak=True` и `target_met=False`.
"""

from __future__ import annotations

import numpy as np

from modules.dsp.metrics import (
    crest_db,
    peak_dbfs,
    reference_crest_db,
    reference_rms_dbfs,
    rms_dbfs,
)

__all__ = ["BUS_TARGET_DBFS", "PEAK_CEILING_DBFS", "stage"]

BUS_TARGET_DBFS = -18.0
PEAK_CEILING_DBFS = -3.0
REFERENCE_WINDOW_SEC = 10.0


def stage(
    x: np.ndarray,
    *,
    target_rms_dbfs: float = BUS_TARGET_DBFS,
    peak_ceiling_dbfs: float = PEAK_CEILING_DBFS,
    sample_rate: int = 44_100,
    window_sec: float = REFERENCE_WINDOW_SEC,
) -> tuple[np.ndarray, dict[str, float | bool]]:
    """Привести опорный участок буфера к целевому RMS, не превысив потолок пика."""
    arr = np.asarray(x, dtype=np.float64)
    reference = reference_rms_dbfs(arr, sample_rate, window_sec)
    in_peak = peak_dbfs(arr)
    if arr.size == 0:
        return arr, {
            "target_rms_dbfs": target_rms_dbfs,
            "reference_rms_dbfs": reference,
            "track_rms_dbfs": rms_dbfs(arr),
            "applied_gain_db": 0.0,
            "limited_by_peak": False,
            "target_met": False,
        }

    gain_db = target_rms_dbfs - reference
    limited = False
    if in_peak + gain_db > peak_ceiling_dbfs:
        gain_db = peak_ceiling_dbfs - in_peak
        limited = True

    out = arr * (10.0 ** (gain_db / 20.0))
    out_reference = reference_rms_dbfs(out, sample_rate, window_sec)
    return out, {
        "target_rms_dbfs": target_rms_dbfs,
        "reference_rms_dbfs": round(reference, 2),
        "output_reference_rms_dbfs": round(out_reference, 2),
        "track_rms_dbfs": round(rms_dbfs(out), 2),
        "input_peak_dbfs": round(in_peak, 2),
        "output_peak_dbfs": round(peak_dbfs(out), 2),
        "crest_db": round(crest_db(out), 2),
        "reference_crest_db": round(reference_crest_db(out, sample_rate, window_sec), 2),
        "applied_gain_db": round(gain_db, 2),
        "limited_by_peak": limited,
        "target_met": abs(out_reference - target_rms_dbfs) <= 0.5,
    }

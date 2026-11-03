# -*- coding: utf-8 -*-
"""modules/mastering/normalize.py — добить громкость готового мастера.

Отдельно от цепи: используется там, где файл уже сведён (polish, повторная
сборка), и новую DSP-окраску применять нельзя — только сходимость по LUFS.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from modules.dsp import metrics
from modules.mastering.chain import _load
from modules.mastering.loudness import _converge_loudness
from modules.mastering.targets import TRUE_PEAK_CEILING


def normalize_master_loudness(
    input_wav: str,
    output_wav: str | None = None,
    target_lufs: float = -14.0,
    ceiling_db: float = TRUE_PEAK_CEILING,
) -> dict[str, Any]:
    """Довести громкость уже готового мастера без новой DSP-окраски."""
    output_wav = output_wav or input_wav
    try:
        y, sr = _load(input_wav)
    except Exception as exc:
        return {"ok": False, "reason": f"read failed: {type(exc).__name__}: {exc}"}
    if y.size == 0:
        return {"ok": False, "reason": "master audio is empty"}

    normalized, info = _converge_loudness(y, sr, target_lufs, ceiling_dbtp=ceiling_db)
    report = metrics.loudness_report(normalized, sr)
    out = Path(output_wav)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), normalized.astype(np.float32), sr, subtype="FLOAT")
    return {
        "ok": True,
        "path": str(out),
        "target_lufs": float(target_lufs),
        "output_lufs": report["lufs"],
        "output_true_peak_dbtp": report["true_peak_dbtp"],
        "output_peak_db": report["peak_dbfs"],  # совместимость с прежним API
        "output_rms_dbfs": report["rms_dbfs"],
        "loudness_mode": "integrated_lufs" if report["lufs_status"] == "ok" else "rms_approximation",
        "sample_rate": sr,
        "channels": report["channels"],
        "report": report,
        "loudness": info,
    }

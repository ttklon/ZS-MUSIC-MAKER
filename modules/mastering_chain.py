# -*- coding: utf-8 -*-
"""modules/mastering_chain.py — legacy-адаптер поверх единого мастеринга.

Раньше здесь жила вторая (независимая) реализация мастеринга: pedalboard-цепь
со своим RMS-фоллбеком, своим потолком и своими метриками. Теперь DSP один —
`modules.mastering` (тон → многополосная компрессия → лимитер −1 dBTP → LUFS).
Этот модуль оставлен только ради старых вызовов и обязан оставаться тонким:

* `process_mastering(...)` — свести вокал (если передан) и отдать мастер движку;
* `normalize_master_loudness(...)` — реэкспорт одноимённой функции движка.

Новый код должен звать `modules.mastering` напрямую.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

_LOG = logging.getLogger(__name__)

__all__ = ["normalize_master_loudness", "process_mastering"]


def _mix_with_vocal(input_wav: str, vocal_path: str, out_wav: str) -> str:
    """Свести бит и вокал штатным микшером (`modules.mix.bus`)."""
    from modules.mix.bus import build_mix

    result = build_mix(input_wav, vocal_path, out_wav)
    if not result.get("ok"):
        _LOG.warning("legacy master mix failed, using dry beat: %s", result.get("reason"))
        return input_wav
    if not result.get("gates_passed"):
        _LOG.warning("legacy master mix gates failed: %s", result.get("gates"))
    return out_wav


def process_mastering(
    input_wav: str,
    output_wav: str,
    vocal_path: str | None = None,
    target_lufs: float = -14.0,
) -> dict[str, Any]:
    """Совместимый вход для God Mode: свести вокал и отмастерить под `target_lufs`."""
    from modules import mastering

    if not Path(input_wav).exists():
        return {"ok": False, "reason": f"input wav not found: {input_wav}"}

    stage_input = input_wav
    if vocal_path and Path(vocal_path).exists():
        stage_input = _mix_with_vocal(input_wav, vocal_path, str(Path(output_wav).with_name("_legacy_mix.wav")))

    result = mastering.master_one(stage_input, output_wav, stand="streaming")
    if not result.get("ok"):
        return {"ok": False, "reason": result.get("reason", "mastering failed")}

    if abs(float(result.get("output_lufs", target_lufs)) - float(target_lufs)) > 0.3:
        result = mastering.normalize_master_loudness(
            output_wav, output_wav, target_lufs=target_lufs
        )
        result.setdefault("engine", "numpy_true_peak_limiter")
    else:
        result["engine"] = "numpy_true_peak_limiter"

    result["applied_gain"] = round(
        float(result.get("output_rms_dbfs", 0.0)) - float(result.get("input_rms_dbfs", 0.0)), 3
    )
    result.setdefault("channels", 2)
    return result


def normalize_master_loudness(
    input_wav: str,
    output_wav: str | None = None,
    target_lufs: float = -14.0,
    ceiling_db: float = -1.0,
) -> dict[str, Any]:
    """Реэкспорт: нормализация громкости живёт в `modules.mastering`."""
    from modules import mastering

    return mastering.normalize_master_loudness(
        input_wav, output_wav, target_lufs=target_lufs, ceiling_db=ceiling_db
    )

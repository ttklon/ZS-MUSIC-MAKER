# -*- coding: utf-8 -*-
"""
modules/vocal_fx/double.py — double-tracking: «второй дубль» без нейросетей.

Вокал слегка растягивается (±0.6 %) и детюнится (±8 центов), затем
подмешивается тихо под основной с pre-delay. Так делают плотный хук на живых
записях; это не RVC и не имитация нейросети.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.vocal_fx.dsp import (
    _OK,
    _detune_cents,
    _fit_len,
    _np,
    _read,
    _resample_linear,
    _rms_db,
    _write,
)


@dataclass
class VocalFxResult:
    ok: bool
    out_wav: str
    engine: str
    double_used: bool
    throw_used: bool
    throws_applied: int
    in_rms_db: float
    out_rms_db: float
    reason: str | None = None


def apply_vocal_double(
    vocal_wav: str,
    out_wav: str,
    double_level_db: float = -10.0,
    detune_cents: float = 8.0,
    time_stretch: float = 0.006,
    pre_delay_ms: float = 22.0,
) -> VocalFxResult:
    """Классический double-tracking: детюн+микро-растянутый дабл под основой."""
    if not _OK:
        return VocalFxResult(
            False,
            "",
            "none",
            False,
            False,
            0,
            -100.0,
            -100.0,
            reason="numpy/soundfile unavailable",
        )
    try:
        y, sr = _read(vocal_wav)
        n = len(y)
        mono = y.mean(axis=1)

        # дабл: детюн + лёгкое растяжение -> «второй голос»
        dbl = _detune_cents(mono, sr, detune_cents)
        dbl = _resample_linear(dbl, 1.0 + time_stretch)
        # pre-delay, чтобы дабл не совпадал покадрово (comb-filter guard)
        pd = max(1, int(sr * pre_delay_ms / 1000.0))
        dbl = _np.concatenate([_np.zeros(pd, dtype="float32"), dbl])
        dbl = _fit_len(dbl, n)
        gain = 10.0 ** (double_level_db / 20.0)

        out = y.copy()
        for c in range(out.shape[1]):
            out[:, c] = out[:, c] + dbl * gain
        # нормализация, чтобы не клиппить
        peak = float(_np.max(_np.abs(out)) + 1e-9)
        if peak > 1.0:
            out = out / peak * 0.98

        _write(out_wav, out, sr)
        return VocalFxResult(
            True,
            out_wav,
            "numpy_double_tracking",
            double_used=True,
            throw_used=False,
            throws_applied=0,
            in_rms_db=_rms_db(y),
            out_rms_db=_rms_db(out),
        )
    except Exception as e:
        return VocalFxResult(
            False, "", "none", False, False, 0, -100.0, -100.0, reason=str(e)
        )

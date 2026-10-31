# -*- coding: utf-8 -*-
"""
modules/vocal_fx/throw.py — delay throw на концах фраз.

По VAD-тишине находится конец фразы, туда бросается ping-pong эхо — оно
заполняет паузу перед хуком и даёт драматургию. Без scipy: задержка
реализована сдвигом буфера.
"""

from __future__ import annotations

from modules.vocal_fx.double import VocalFxResult
from modules.vocal_fx.dsp import (
    _OK,
    _find_phrase_ends,
    _np,
    _read,
    _rms_db,
    _write,
)


def apply_delay_throw(
    vocal_wav: str,
    out_wav: str,
    delay_ms: float = 320.0,
    feedback: float = 0.32,
    throw_level_db: float = -9.0,
    silence_db: float = -40.0,
    ping_pong: bool = True,
) -> VocalFxResult:
    """Delay throw: эхо-бросок в паузах на концах фраз (заполняет воздух)."""
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
        ends = _find_phrase_ends(mono, sr, silence_db=silence_db)
        d = max(1, int(sr * delay_ms / 1000.0))
        gain = 10.0 ** (throw_level_db / 20.0)

        wet = _np.zeros_like(y)
        throws = 0
        for e in ends:
            # источник броска — короткий хвост фразы перед паузой
            tail_s = max(0, e - int(sr * 0.25))
            tail = y[tail_s:e].copy()
            if len(tail) < 16:
                continue
            throws += 1
            pos = e
            level = gain
            taps = 0
            while pos < n and level > 0.02 and taps < 5:
                seg = tail * level
                room = min(len(seg), n - pos)
                if ping_pong and wet.shape[1] >= 2:
                    # ping-pong: чередуем каналы по номеру отражения
                    ch = taps % wet.shape[1]
                    seg2 = _np.zeros_like(seg)
                    seg2[:, ch] = seg[:, ch]
                    seg2[:, 1 - ch] = seg[:, 1 - ch] * 0.7
                    wet[pos : pos + room] += seg2[:room]
                else:
                    wet[pos : pos + room] += seg[:room]
                pos += d
                level *= feedback
                taps += 1

        out = y + wet
        peak = float(_np.max(_np.abs(out)) + 1e-9)
        if peak > 1.0:
            out = out / peak * 0.98
        _write(out_wav, out, sr)
        return VocalFxResult(
            True,
            out_wav,
            "numpy_delay_throw",
            double_used=False,
            throw_used=True,
            throws_applied=throws,
            in_rms_db=_rms_db(y),
            out_rms_db=_rms_db(out),
        )
    except Exception as e:
        return VocalFxResult(
            False, "", "none", False, False, 0, -100.0, -100.0, reason=str(e)
        )

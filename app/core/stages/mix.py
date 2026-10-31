# -*- coding: utf-8 -*-
"""
app/core/stages/mix.py — Микс: bus = бит + вокал, затем сайдчейн по кику.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _mix_beat_and_vocal(
    beat_wav: str, vocal_wav: str | None, out_wav: str, vocal_gain_db: float = -3.0
) -> str | None:
    """
    v17: честный микс bus = beat + vocal (HP80 на вокале, ресемпл,
    моно→стерео, пик-safe). До этого фикса вокал вообще не подмешивался.
    """
    try:
        import numpy as np
        import soundfile as sf

        beat, sr_b = sf.read(beat_wav, always_2d=True)
        if not vocal_wav or not Path(vocal_wav).exists():
            sf.write(out_wav, beat, sr_b)
            return out_wav
        voc, sr_v = sf.read(vocal_wav, always_2d=True)
        if sr_v != sr_b:
            try:
                from scipy.signal import resample_poly

                voc = np.stack(
                    [resample_poly(voc[:, c], sr_b, sr_v) for c in range(voc.shape[1])],
                    axis=1,
                )
            except Exception:
                voc = voc[: beat.shape[0]]
        if voc.shape[1] == 1 and beat.shape[1] >= 2:
            voc = np.repeat(voc, 2, axis=1)
        n = beat.shape[0]
        if voc.shape[0] < n:
            pad = np.zeros((n - voc.shape[0], voc.shape[1]), dtype=voc.dtype)
            voc = np.concatenate([voc, pad], axis=0)
        else:
            voc = voc[:n]
        try:
            from scipy.signal import butter, sosfilt

            sos = butter(4, 80, btype="high", fs=sr_b, output="sos")
            voc = np.stack(
                [sosfilt(sos, voc[:, c]) for c in range(voc.shape[1])], axis=1
            )
        except Exception:
            pass
        gain = 10 ** (vocal_gain_db / 20.0)
        bus = beat.astype("float32") + voc.astype("float32") * gain
        peak = float(np.max(np.abs(bus)) + 1e-9)
        if peak > 0.98:
            bus = bus / peak * 0.98
        Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
        sf.write(out_wav, bus, sr_b)
        return out_wav
    except Exception:
        try:
            import shutil

            shutil.copy(beat_wav, out_wav)
            return out_wav
        except Exception:
            return None


def _stage_mix_and_sidechain(
    beat_wav: str, voice_wav: str | None, out_dir: Path
) -> dict[str, Any]:
    """
    v17 FIX (P0): раньше sidechain(beat, beat) дакал бит сам собой,
    вокал в bus вообще не попадал. Теперь bus = beat + vocal, потом
    sidechain по кику от бита.
    """
    try:
        raw_mix = str(out_dir / "mix_raw.wav")
        _mix_beat_and_vocal(beat_wav, voice_wav, raw_mix)
        from modules import sidechain

        ducked = str(out_dir / "mix_ducked.wav")
        r = sidechain.apply_sidechain(raw_mix, beat_wav, ducked, intensity=0.5)
        if isinstance(r, dict) and r.get("out_wav"):
            return r
        return {
            "ok": True,
            "out_wav": raw_mix,
            "engine": "raw_mix_no_sidechain",
            "fallback_used": True,
            "reason": "sidechain unavailable; raw mix returned",
        }
    except Exception as e:
        return {"ok": False, "reason": str(e)}

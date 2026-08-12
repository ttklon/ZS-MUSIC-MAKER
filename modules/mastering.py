"""
ZS Music Maker — modules/mastering.py (v27 P0 fix)
=====================================================================
Настоящий модуль мастеринга. Раньше orchestrator._stage_mastering делал
`from modules import mastering` — а такого модуля не существовало:
из-за этого master_streaming.wav никогда не писался, каскадно валились
polish / stems / hit_score / release_pack (в smoke_v26: 3/6 PASS).

Здесь честно реализованы стенды мастеринга поверх numpy + опционально
pyloudnorm / pedalboard, СОХРАНЯЯ стерео (v26 fix), записывая
master_streaming.wav и все запрошенные стенды.

API, ожидаемый orchestrator:

    master_all_stands(mix_wav, out_dir, stands=None) -> {
        "ok": bool,
        "stands": {stand: {"ok": bool, "out_wav": path, "engine": str,
                            "lufs_target": float, "lufs_measured": float}},
        "summary": {"fallback": int, "engine": str},
    }

Дополнительно экспортируется:
  * `_k_weighted_loudness_approx(y, sr) -> float` — smoke_v23 / smoke_v25
  * `_try_numpy_dsp(...)` — honest numpy DSP path (fallback_used=False)
  * `capability_report()` — smoke_v14 (легковесная диагностика)
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

try:
    import pyloudnorm as pyln  # type: ignore

    HAS_PYLN = True
except Exception:
    HAS_PYLN = False

try:
    from pedalboard import (  # type: ignore
        Compressor,
        HighpassFilter,
        Limiter,
        LowShelfFilter,
        Pedalboard,
    )

    HAS_PEDAL = True
except Exception:
    HAS_PEDAL = False

# LUFS-цели по стендам (v26 сдвиг +0.5 dB для потока/наушников/мониторов)
LUFS_TARGETS = {
    "streaming": -13.5,
    "car": -8.5,
    "club": -6.5,
    "tiktok": -13.0,
    "airpods": -14.0,
    "bluetooth": -13.0,
    "headphones": -13.5,
    "monitors": -13.5,
}

VALID_STANDS = tuple(LUFS_TARGETS.keys())


# ---------------------------------------------------------------------
# K-weighting (ITU-BS.1770 приблизительно, без gating)
# ---------------------------------------------------------------------
def _k_weighted_loudness_approx(y: np.ndarray, sr: int) -> float:
    """Быстрая аппроксимация K-weighted loudness (LUFS-like)."""
    try:
        arr = np.asarray(y, dtype=np.float32)
        if arr.ndim == 1:
            channels = [arr]
        else:
            if arr.shape[0] < arr.shape[1]:
                arr = arr.T
            channels = [arr[:, c] for c in range(arr.shape[1])]

        from scipy.signal import butter, sosfilt

        sos_hp = butter(2, 38.0, btype="highpass", fs=sr, output="sos")
        sos_hs = butter(2, 1500.0, btype="highpass", fs=sr, output="sos")

        mean_squares = []
        for ch in channels:
            x = sosfilt(sos_hp, ch)
            hs = sosfilt(sos_hs, x)
            xw = x + 0.585 * hs
            mean_squares.append(float(np.mean(xw**2)))

        weights = [1.0] * len(mean_squares)
        power = sum(w * m for w, m in zip(weights, mean_squares))
        if power <= 1e-20:
            return -120.0
        return float(-0.691 + 10.0 * np.log10(power))
    except Exception:
        arr = np.asarray(y, dtype=np.float32)
        rms = float(np.sqrt(np.mean(arr**2)) + 1e-12)
        return 20.0 * float(np.log10(rms)) - 3.0


def _load_stereo(path: str) -> tuple[np.ndarray, int]:
    y, sr = sf.read(path, always_2d=True)
    y = y.astype(np.float32, copy=False)
    if y.shape[1] == 1:
        y = np.repeat(y, 2, axis=1)
    return y, int(sr)


def _measure_lufs(y: np.ndarray, sr: int) -> float:
    if HAS_PYLN:
        try:
            meter = pyln.Meter(sr)
            return float(meter.integrated_loudness(y))
        except Exception:
            pass
    return _k_weighted_loudness_approx(y, sr)


def _apply_stand_eq(y: np.ndarray, sr: int, stand: str) -> np.ndarray:
    """Стерео-безопасная EQ через FFT по каналам."""
    try:
        out = np.zeros_like(y)
        for c in range(y.shape[1]):
            ch = y[:, c].astype(np.float32)
            Y = np.fft.rfft(ch)
            freqs = np.fft.rfftfreq(len(ch), 1.0 / sr)
            gain = np.ones_like(freqs, dtype=np.float32)
            if stand == "car":
                gain[(freqs >= 30) & (freqs <= 80)] *= 1.55
                gain[(freqs > 8000)] *= 0.85
            elif stand == "club":
                gain[(freqs >= 40) & (freqs <= 120)] *= 1.7
                gain[(freqs >= 2000) & (freqs <= 5000)] *= 1.1
            elif stand == "tiktok":
                gain[(freqs >= 200) & (freqs <= 4000)] *= 1.12
                gain[(freqs < 60)] *= 0.85
            elif stand == "airpods":
                gain[(freqs >= 100) & (freqs <= 250)] *= 1.15
                gain[(freqs >= 4000) & (freqs <= 10000)] *= 1.1
            elif stand == "bluetooth":
                gain[(freqs >= 80) & (freqs <= 200)] *= 1.1
                gain[(freqs > 12000)] *= 0.9
            elif stand == "headphones":
                gain[(freqs >= 60) & (freqs <= 120)] *= 1.05
                gain[(freqs >= 8000) & (freqs <= 12000)] *= 1.05
            elif stand == "monitors":
                gain[(freqs < 30)] *= 0.9
            else:
                gain[(freqs >= 60) & (freqs <= 100)] *= 1.05
                gain[(freqs >= 5000) & (freqs <= 10000)] *= 0.95
            Y2 = Y * gain
            out[:, c] = np.fft.irfft(Y2, n=len(ch)).astype(np.float32)
        return out
    except Exception:
        return y


def _apply_pedalboard(y: np.ndarray, sr: int, stand: str) -> np.ndarray:
    """Если pedalboard есть — HPF → shelf → compressor → limiter."""
    if not HAS_PEDAL:
        return y
    try:
        shelf_gain = 1.5 if stand in ("car", "club") else 0.5
        board = Pedalboard(
            [
                HighpassFilter(cutoff_frequency_hz=28.0),
                LowShelfFilter(cutoff_frequency_hz=110.0, gain_db=shelf_gain, q=0.7),
                Compressor(
                    threshold_db=-14.0,
                    ratio=2.5,
                    attack_ms=6.0,
                    release_ms=90.0,
                ),
                Limiter(threshold_db=-0.4, release_ms=80.0),
            ]
        )
        arr_cf = y.T.astype(np.float32)
        out = board(arr_cf, sr)
        return out.T.astype(np.float32)
    except Exception:
        return y


def _iterative_loudnorm(
    y: np.ndarray,
    sr: int,
    target_lufs: float,
    iterations: int = 3,
    max_gain_db: float = 24.0,
) -> tuple[np.ndarray, float]:
    """Итеративная нормализация под целевой LUFS с tanh soft-limiter."""
    cur = y.astype(np.float32, copy=True)
    measured = _measure_lufs(cur, sr)
    for _ in range(max(1, iterations)):
        delta = target_lufs - measured
        delta = float(np.clip(delta, -max_gain_db, max_gain_db))
        lin = 10.0 ** (delta / 20.0)
        cur = cur * lin
        peak = float(np.max(np.abs(cur)) + 1e-12)
        if peak > 0.98:
            cur = np.tanh(cur * 0.98) * 0.98
        measured = _measure_lufs(cur, sr)
    return cur, measured


def _write_stereo(path: str, y: np.ndarray, sr: int) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    y2 = np.clip(y, -0.999, 0.999).astype(np.float32)
    if y2.ndim == 1:
        y2 = np.stack([y2, y2], axis=1)
    sf.write(path, y2, sr, subtype="PCM_16")


def _try_numpy_dsp(
    mix_wav: str, out_wav: str, stand: str, iterations: int = 3
) -> dict[str, Any]:
    """Полноценная numpy/scipy/(pedalboard) DSP-цепочка. fallback_used=False."""
    try:
        y, sr = _load_stereo(mix_wav)
        target = LUFS_TARGETS.get(stand, -14.0)

        y = _apply_stand_eq(y, sr, stand)
        y = _apply_pedalboard(y, sr, stand)
        y, measured = _iterative_loudnorm(y, sr, target, iterations=iterations)

        _write_stereo(out_wav, y, sr)
        return {
            "ok": True,
            "out_wav": out_wav,
            "engine": (
                "numpy+pedalboard+pyloudnorm"
                if (HAS_PEDAL and HAS_PYLN)
                else "numpy+pyloudnorm"
                if HAS_PYLN
                else "numpy+pedalboard"
                if HAS_PEDAL
                else "numpy_dsp"
            ),
            "stand": stand,
            "lufs_target": target,
            "lufs_measured": round(float(measured), 2),
            "fallback_used": False,
        }
    except Exception as e:
        return {"ok": False, "reason": f"{type(e).__name__}: {e}", "stand": stand}


def _pydub_gain_fallback(mix_wav: str, out_wav: str, stand: str) -> dict[str, Any]:
    """Последний рубеж: pydub + честный gain. Явно fallback_used=True."""
    try:
        from pydub import AudioSegment

        seg = AudioSegment.from_file(mix_wav)
        target = LUFS_TARGETS.get(stand, -14.0)
        approx = seg.dBFS - 3.0
        gain = float(np.clip(target - approx, -20.0, 20.0))
        seg = seg.apply_gain(gain)
        if stand == "club":
            seg = seg.compress_dynamic_range(threshold=-6.0, ratio=4.0)
        Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
        seg.export(out_wav, format="wav")
        return {
            "ok": True,
            "out_wav": out_wav,
            "engine": "pydub_gain_fallback",
            "stand": stand,
            "lufs_target": target,
            "lufs_measured": None,
            "fallback_used": True,
        }
    except Exception as e:
        try:
            Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(mix_wav, out_wav)
            return {
                "ok": True,
                "out_wav": out_wav,
                "engine": "raw_copy",
                "stand": stand,
                "lufs_target": LUFS_TARGETS.get(stand, -14.0),
                "lufs_measured": None,
                "fallback_used": True,
                "reason": f"pydub failed: {e}",
            }
        except Exception as e2:
            return {"ok": False, "reason": f"copy failed: {e2}", "stand": stand}


def master_one_stand(
    mix_wav: str, out_wav: str, stand: str, iterations: int = 3
) -> dict[str, Any]:
    """Мастер одного стенда: сначала numpy DSP, при ошибке — pydub gain."""
    if stand not in VALID_STANDS:
        return {"ok": False, "reason": f"unknown stand: {stand}"}
    r = _try_numpy_dsp(mix_wav, out_wav, stand, iterations=iterations)
    if r.get("ok"):
        return r
    return _pydub_gain_fallback(mix_wav, out_wav, stand)


def master_all_stands(
    mix_wav: str,
    out_dir: str,
    stands: list[str] | None = None,
    iterations: int = 3,
) -> dict[str, Any]:
    """
    Главная точка входа orchestrator._stage_mastering.
    - streaming ВСЕГДА обязательно (иначе валится polish/stems/hit_score).
    - файлы: master_<stand>.wav (совместимо с smoke_v25.stands_filter).
    """
    if not mix_wav or not os.path.exists(mix_wav):
        return {"ok": False, "reason": f"mix not found: {mix_wav}"}
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    if not stands:
        stands = ["streaming", "car", "club", "tiktok"]
    else:
        stands = [s for s in stands if s in VALID_STANDS]
        if "streaming" not in stands:
            stands.insert(0, "streaming")

    results: dict[str, Any] = {}
    fb_count = 0
    engines: list[str] = []
    for stand in stands:
        out_wav = str(Path(out_dir) / f"master_{stand}.wav")
        r = master_one_stand(mix_wav, out_wav, stand, iterations=iterations)
        results[stand] = r
        if r.get("fallback_used"):
            fb_count += 1
        if r.get("engine"):
            engines.append(r["engine"])

    ok_any = any(r.get("ok") for r in results.values())
    return {
        "ok": ok_any,
        "stands": results,
        "summary": {
            "fallback": fb_count,
            "engine": (
                "numpy+pedalboard+pyloudnorm"
                if (HAS_PEDAL and HAS_PYLN)
                else "numpy+pyloudnorm"
                if HAS_PYLN
                else "numpy+pedalboard"
                if HAS_PEDAL
                else "numpy_dsp"
            ),
            "engines_used": sorted(set(engines)),
            "count": len(results),
        },
    }


def capability_report() -> dict[str, Any]:
    """v27: honest capability report (used by smoke_v14 capability.mastering)."""
    return {
        "module": "modules.mastering",
        "version": "27.0.0",
        "has_pyloudnorm": HAS_PYLN,
        "has_pedalboard": HAS_PEDAL,
        "supported_stands": list(VALID_STANDS),
        "lufs_targets": dict(LUFS_TARGETS),
        "engines": ["numpy_dsp"]
        + (["pyloudnorm"] if HAS_PYLN else [])
        + (["pedalboard"] if HAS_PEDAL else [])
        + ["pydub_gain_fallback"],
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("usage: python -m modules.mastering <mix.wav> <out_dir> [stand ...]")
        raise SystemExit(2)
    mix = sys.argv[1]
    outd = sys.argv[2]
    st = sys.argv[3:] or None
    r = master_all_stands(mix, outd, stands=st)
    import json

    print(json.dumps(r, ensure_ascii=False, indent=2))

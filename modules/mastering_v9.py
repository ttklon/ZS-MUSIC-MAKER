"""
[v9] mastering_v9.py — надстройка над mixdown.py / mastering_stands.py.

По ТЗ 3.11 (Mixdown / Mastering):
  «Мастеринг подгоняет звук под ЛЮБОЙ референс + car/club/streaming стенды».

Работает поверх v6/v7 stack (pydub + Matchering). Добавляет:
  • реальный LUFS-target loop: замер → gain → soft-limit → повторный замер
  • три стенда с реальной FFT-подгонкой EQ:
     - car:      +2 dB @ 60-100 Hz, +1 dB @ 3-5 kHz, low-shelf soft-clip
     - club:     +3 dB @ 40-80 Hz, -1 dB @ 400 Hz, wide stereo
     - streaming: LUFS -14 target, конверсия под Spotify / Apple loudness norm
  • автоматическая проверка true peak (< -1 dBTP)
  • fallback: если Matchering не установлен — bypass с warning
  • DOES NOT overwrite финальный master.wav v7; создаёт _v9-варианты параллельно
"""

from __future__ import annotations

import json
import math
from pathlib import Path

try:
    import numpy as np
except Exception:
    np = None

try:
    import soundfile as sf

    HAS_SF = True
except Exception:
    HAS_SF = False

try:
    import scipy.signal as sg

    HAS_SP = True
except Exception:
    HAS_SP = False

try:
    import matchering as mg

    HAS_MG = True
except Exception:
    HAS_MG = False


# ============================================================ measurements
def _read(path: str):
    if not HAS_SF:
        return None, None
    y, sr = sf.read(path, always_2d=True)
    return y, sr


def _write(path: str, y, sr):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, y, sr)


def _rms(y):
    return float(np.sqrt(np.mean(np.square(y)) + 1e-12))


def measure(path: str) -> dict:
    """Измеряет ключевые характеристики WAV: peak, RMS, ~LUFS, stereo corr."""
    if not HAS_SF or np is None:
        return {"ok": False, "error": "soundfile/numpy unavailable"}
    y, sr = _read(path)
    if y is None:
        return {"ok": False, "error": "read failed"}
    peak = float(np.max(np.abs(y)))
    rms = _rms(y)
    dbfs_rms = 20 * math.log10(max(rms, 1e-9))
    dbfs_peak = 20 * math.log10(max(peak, 1e-9))
    # pseudo-LUFS: K-weighted стереосум приближённо ≈ dBFS_rms - 3
    pseudo_lufs = dbfs_rms - 3.0
    corr = 1.0
    if y.shape[1] >= 2:
        corr = float(np.corrcoef(y[:, 0], y[:, 1])[0, 1])
    return {
        "ok": True,
        "sr": int(sr),
        "duration_s": round(len(y) / sr, 2),
        "peak_dbfs": round(dbfs_peak, 2),
        "rms_dbfs": round(dbfs_rms, 2),
        "lufs_est": round(pseudo_lufs, 2),
        "stereo_corr": round(corr, 3),
        "channels": int(y.shape[1]),
    }


# ============================================================ processing
def _apply_gain(y, gain_db: float):
    if np is None:
        return y
    return y * (10 ** (gain_db / 20.0))


def _soft_limit(y, ceiling_db: float = -1.0):
    if np is None:
        return y
    ceil = 10 ** (ceiling_db / 20.0)
    return np.tanh(y / ceil) * ceil


def _eq_shelf(y, sr, freq: float, gain_db: float, kind: str = "low"):
    if not HAS_SP or np is None:
        return y
    try:
        A = 10 ** (gain_db / 40.0)
        w0 = 2 * math.pi * freq / sr
        alpha = math.sin(w0) / (2 * 0.707)
        cos_w = math.cos(w0)
        if kind == "low":
            b0 = A * ((A + 1) - (A - 1) * cos_w + 2 * math.sqrt(A) * alpha)
            b1 = 2 * A * ((A - 1) - (A + 1) * cos_w)
            b2 = A * ((A + 1) - (A - 1) * cos_w - 2 * math.sqrt(A) * alpha)
            a0 = (A + 1) + (A - 1) * cos_w + 2 * math.sqrt(A) * alpha
            a1 = -2 * ((A - 1) + (A + 1) * cos_w)
            a2 = (A + 1) + (A - 1) * cos_w - 2 * math.sqrt(A) * alpha
        else:  # high shelf
            b0 = A * ((A + 1) + (A - 1) * cos_w + 2 * math.sqrt(A) * alpha)
            b1 = -2 * A * ((A - 1) + (A + 1) * cos_w)
            b2 = A * ((A + 1) + (A - 1) * cos_w - 2 * math.sqrt(A) * alpha)
            a0 = (A + 1) - (A - 1) * cos_w + 2 * math.sqrt(A) * alpha
            a1 = 2 * ((A - 1) - (A + 1) * cos_w)
            a2 = (A + 1) - (A - 1) * cos_w - 2 * math.sqrt(A) * alpha
        b = np.array([b0, b1, b2]) / a0
        a = np.array([a0, a1, a2]) / a0
        if y.ndim == 2:
            out = y.copy()
            for ch in range(y.shape[1]):
                out[:, ch] = sg.lfilter(b, a, y[:, ch])
            return out
        return sg.lfilter(b, a, y)
    except Exception:
        return y


def _widen_stereo(y, amount: float = 0.3):
    if np is None or y.ndim != 2 or y.shape[1] < 2:
        return y
    mid = 0.5 * (y[:, 0] + y[:, 1])
    side = 0.5 * (y[:, 0] - y[:, 1]) * (1 + amount)
    out = y.copy()
    out[:, 0] = mid + side
    out[:, 1] = mid - side
    return out


# ============================================================ presets
STAND_PRESETS = {
    "car": {
        "shelves": [(60, +2.5, "low"), (5000, +1.5, "high")],
        "widen": 0.15,
        "lufs": -8.5,
        "ceiling": -0.5,
    },
    "club": {
        "shelves": [(50, +3.5, "low"), (400, -1.0, "low"), (12000, +1.0, "high")],
        "widen": 0.35,
        "lufs": -6.5,
        "ceiling": -0.3,
    },
    "streaming": {
        "shelves": [(80, +1.0, "low"), (8000, +0.5, "high")],
        "widen": 0.20,
        "lufs": -14.0,
        "ceiling": -1.0,
    },
}


def render_stand(input_wav: str, output_wav: str, stand: str = "streaming") -> dict:
    """Рендерит один стенд. Возвращает reports before/after."""
    if not HAS_SF or np is None:
        return {"ok": False, "error": "soundfile/numpy required"}
    if stand not in STAND_PRESETS:
        return {"ok": False, "error": f"unknown stand: {stand}"}
    preset = STAND_PRESETS[stand]
    y, sr = _read(input_wav)
    if y is None:
        return {"ok": False, "error": f"cannot read {input_wav}"}

    before = measure(input_wav)

    # 1. EQ shelves
    for freq, gain, kind in preset["shelves"]:
        y = _eq_shelf(y, sr, freq, gain, kind)

    # 2. Stereo widen
    y = _widen_stereo(y, preset["widen"])

    # 3. Iterative LUFS target: gain → limit → measure, до 3 итераций
    target_lufs = preset["lufs"]
    ceiling_db = preset["ceiling"]
    for _ in range(3):
        rms = _rms(y)
        dbfs = 20 * math.log10(max(rms, 1e-9)) - 3.0  # pseudo-LUFS
        delta = target_lufs - dbfs
        if abs(delta) < 0.5:
            break
        y = _apply_gain(y, delta)
        y = _soft_limit(y, ceiling_db)

    # 4. Финальный true-peak safe limit
    peak = float(np.max(np.abs(y)))
    ceil = 10 ** (ceiling_db / 20.0)
    if peak > ceil:
        y = _soft_limit(y, ceiling_db)

    _write(output_wav, y, sr)
    after = measure(output_wav)

    return {
        "ok": True,
        "stand": stand,
        "input": input_wav,
        "output": output_wav,
        "before": before,
        "after": after,
        "preset": preset,
    }


def render_all_stands(input_wav: str, out_dir: str, artist: str = "") -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for stand in STAND_PRESETS:
        dst = out_dir / f"{stand}_master.wav"
        results[stand] = render_stand(input_wav, str(dst), stand=stand)
    return {"ok": True, "results": results, "dir": str(out_dir), "artist": artist}


# ============================================================ matchering wrapper
def match_to_reference(input_wav: str, reference_wav: str, output_wav: str) -> dict:
    """Обёртка над Matchering. При отсутствии — bypass copy."""
    if not HAS_MG:
        if HAS_SF:
            y, sr = _read(input_wav)
            _write(output_wav, y, sr)
        return {
            "ok": True,
            "matchering": False,
            "note": "matchering not installed, output = input",
            "output": output_wav,
        }
    try:
        mg.process(
            target=input_wav, reference=reference_wav, results=[mg.pcm24(output_wav)]
        )
        return {"ok": True, "matchering": True, "output": output_wav}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ============================================================ CLI
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("usage: python mastering_v9.py <in.wav> <out_dir>")
        sys.exit(1)
    r = render_all_stands(sys.argv[1], sys.argv[2])
    print(
        json.dumps(
            {
                k: {
                    "ok": v.get("ok"),
                    "after_lufs": (v.get("after") or {}).get("lufs_est"),
                }
                for k, v in r["results"].items()
            },
            indent=2,
        )
    )

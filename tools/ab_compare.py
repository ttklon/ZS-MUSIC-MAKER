"""
ZS Music Maker v15 — tools/ab_compare.py
==============================================
TZ раздел 20 (A/B сравнение). Сравнивает пользовательский трек
с референсом:
  - LUFS integrated / short-term
  - True Peak (approx)
  - RMS / peak
  - Spectrogram (PNG, side-by-side)
  - Stereo width (mid/side correlation)
  - Duration match
Возвращает JSON и PNG.

CLI: python tools/ab_compare.py user.wav ref.wav [--out dir]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import numpy as np
    import soundfile as sf
except Exception as exc:
    print(f"[ab_compare] core dependencies missing: {exc}", file=sys.stderr)
    raise

try:
    import pyloudnorm as pyln
except ImportError:
    pyln = None

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    HAS_PLT = True
except Exception:
    HAS_PLT = False


def _load_stereo(path: str):
    data, sr = sf.read(path, always_2d=False)
    if data.ndim == 1:
        data = np.stack([data, data], axis=1)
    return data.astype(np.float32), sr


def _lufs(data, sr):
    try:
        meter = pyln.Meter(sr)
        return float(meter.integrated_loudness(data))
    except Exception:
        return None


def _true_peak_db(data):
    peak = float(np.max(np.abs(data))) if data.size else 0.0
    if peak <= 0:
        return -120.0
    return 20.0 * np.log10(peak)


def _stereo_width(data):
    if data.ndim < 2 or data.shape[1] < 2:
        return 0.0
    L, R = data[:, 0], data[:, 1]
    # correlation
    if np.std(L) < 1e-9 or np.std(R) < 1e-9:
        return 0.0
    c = float(np.corrcoef(L, R)[0, 1])
    return 1.0 - abs(c)  # ширина = 1 - abs corr


def _spectrogram(data, sr, out_png: Path, title: str):
    if not HAS_PLT:
        return False
    mono = data.mean(axis=1) if data.ndim > 1 else data
    # STFT
    n_fft = 2048
    hop = 512
    # numpy-based simple STFT
    from numpy.lib.stride_tricks import sliding_window_view

    if len(mono) < n_fft:
        return False
    window = np.hanning(n_fft)
    frames = sliding_window_view(mono, n_fft)[::hop]
    spec = np.abs(np.fft.rfft(frames * window, axis=1)).T
    spec_db = 20.0 * np.log10(spec + 1e-9)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.imshow(
        spec_db,
        aspect="auto",
        origin="lower",
        extent=[0, len(mono) / sr, 0, sr / 2 / 1000],
        cmap="viridis",
        vmin=-80,
        vmax=0,
    )
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Freq (kHz)")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out_png, dpi=100)
    plt.close(fig)
    return True


def compare(user_wav: str, ref_wav: str, out_dir: str) -> dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    u_data, u_sr = _load_stereo(user_wav)
    r_data, r_sr = _load_stereo(ref_wav)
    u_lufs = _lufs(u_data, u_sr)
    r_lufs = _lufs(r_data, r_sr)
    u_tp = _true_peak_db(u_data)
    r_tp = _true_peak_db(r_data)
    u_rms = float(np.sqrt(np.mean(u_data**2)))
    r_rms = float(np.sqrt(np.mean(r_data**2)))
    u_w = _stereo_width(u_data)
    r_w = _stereo_width(r_data)
    u_dur = u_data.shape[0] / u_sr
    r_dur = r_data.shape[0] / r_sr

    u_png = out / "spec_user.png"
    r_png = out / "spec_ref.png"
    _spectrogram(u_data, u_sr, u_png, "USER — spectrogram")
    _spectrogram(r_data, r_sr, r_png, "REF  — spectrogram")

    # Side-by-side combined
    combo_png = None
    if HAS_PLT:
        try:
            combo_png = out / "ab_combined.png"
            fig, axes = plt.subplots(2, 1, figsize=(12, 6))
            for ax, path, title in ((axes[0], u_png, "USER"), (axes[1], r_png, "REF")):
                if path.exists():
                    img = plt.imread(path)
                    ax.imshow(img)
                    ax.axis("off")
                    ax.set_title(title)
            fig.tight_layout()
            fig.savefig(combo_png, dpi=100)
            plt.close(fig)
        except Exception:
            combo_png = None

    result = {
        "user": {
            "path": user_wav,
            "sr": u_sr,
            "duration_sec": round(u_dur, 3),
            "lufs_integrated": u_lufs,
            "true_peak_dbfs": u_tp,
            "rms": u_rms,
            "stereo_width": u_w,
        },
        "ref": {
            "path": ref_wav,
            "sr": r_sr,
            "duration_sec": round(r_dur, 3),
            "lufs_integrated": r_lufs,
            "true_peak_dbfs": r_tp,
            "rms": r_rms,
            "stereo_width": r_w,
        },
        "delta": {
            "lufs": (
                round(u_lufs - r_lufs, 2)
                if u_lufs is not None and r_lufs is not None
                else None
            ),
            "true_peak_db": round(u_tp - r_tp, 2),
            "rms": round(u_rms - r_rms, 4),
            "stereo_width": round(u_w - r_w, 3),
            "duration_sec": round(u_dur - r_dur, 3),
        },
        "spectrograms": {
            "user": str(u_png) if u_png.exists() else None,
            "ref": str(r_png) if r_png.exists() else None,
            "combined": str(combo_png) if combo_png else None,
        },
        "verdict": _verdict(u_lufs, r_lufs, u_tp, r_tp, u_w, r_w),
    }
    (out / "ab_report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


def _verdict(u_l, r_l, u_tp, r_tp, u_w, r_w):
    notes = []
    if u_l is not None and r_l is not None:
        d = u_l - r_l
        if abs(d) < 1.0:
            notes.append(f"✅ LUFS: почти в цель ({d:+.1f}dB)")
        elif d < -1:
            notes.append(f"⚠️ USER тише на {-d:.1f}dB")
        else:
            notes.append(f"⚠️ USER громче на {d:.1f}dB")
    if u_tp - r_tp > 0.3:
        notes.append("⚠️ USER пикует выше — возможен клиппинг")
    if abs(u_w - r_w) > 0.15:
        notes.append(f"⚠️ Стерео-ширина отличается на {u_w-r_w:+.2f}")
    if not notes:
        notes.append("✅ Треки близки по метрикам")
    return notes


def main() -> int:
    p = argparse.ArgumentParser(description="Compare a user WAV against a reference WAV")
    p.add_argument("user_wav")
    p.add_argument("ref_wav")
    p.add_argument("--out", default="output/ab_compare")
    a = p.parse_args()
    if pyln is None:
        print("[ab_compare] optional dependency missing: pyloudnorm", file=sys.stderr)
        return 2
    r = compare(a.user_wav, a.ref_wav, a.out)
    # Печатаем без spectrograms полных путей (короткая версия)
    print(
        json.dumps(
            {
                "delta": r["delta"],
                "verdict": r["verdict"],
                "report_path": str(Path(a.out) / "ab_report.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

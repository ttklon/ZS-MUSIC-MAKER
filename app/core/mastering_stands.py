"""
[v7] mastering_stands.py — три виртуальных стенда прослушивания.

Каждый стенд — отдельная EQ+компрессия под свою среду:
  🚗 car       — буст саба (30-80 Гц), лёгкое ограничение верха
  🎧 club      — жирный саб + громкость, легкий boost 60 Гц
  📱 streaming — нейтральный, LUFS ~-14, лёгкий de-esser

Возвращает {stand_name: path_to_wav}.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "stands"
OUT.mkdir(parents=True, exist_ok=True)


def _apply_eq(y, sr: int, stand: str):
    """Простая EQ через FFT. Не для боевого DSP — только приблизительно."""
    try:
        import numpy as np

        Y = np.fft.rfft(y)
        freqs = np.fft.rfftfreq(len(y), 1 / sr)
        gain = np.ones_like(freqs, dtype="float32")
        if stand == "car":
            gain[(freqs >= 30) & (freqs <= 80)] *= 1.6
            gain[freqs > 10000] *= 0.85
        elif stand == "club":
            gain[(freqs >= 40) & (freqs <= 120)] *= 1.8
            gain[(freqs >= 2000) & (freqs <= 5000)] *= 1.15
        elif stand == "streaming":
            gain[(freqs >= 60) & (freqs <= 100)] *= 1.05
            gain[(freqs >= 5000) & (freqs <= 10000)] *= 0.9
        Y2 = Y * gain
        y2 = np.fft.irfft(Y2, n=len(y)).astype("float32")
        peak = float(np.max(np.abs(y2))) + 1e-9
        y2 = y2 / peak * 0.95
        return y2
    except Exception:
        return y


def render_stands(master_path: str, stands: list | None = None) -> dict:
    """
    Из мастер-WAV делает 3 варианта под стенды.
    stands — список из ['car','club','streaming']; None = все три.
    """
    if not master_path or not os.path.exists(master_path):
        return {}
    stands = stands or ["car", "club", "streaming"]
    result = {}
    try:
        import soundfile as sf

        y, sr = sf.read(master_path, always_2d=False)
        # v27 FIX: НЕ делаем монодаунмикс — это убивало стерео-ширину мастера.
        # EQ однополюсный, каналонезависимый: применяем к каждому каналу.
        for stand in stands:
            y2 = _apply_eq(y, sr, stand)
            out_path = OUT / f"{stand}_master.wav"
            sf.write(str(out_path), y2, sr)
            result[stand] = str(out_path)
    except Exception as e:
        print(f"[mastering_stands] {e}")
    return result


if __name__ == "__main__":
    print("mastering_stands v7 ready")

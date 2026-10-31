# -*- coding: utf-8 -*-
"""
modules/video_edit/audio.py — анализ мастера без тяжёлых зависимостей.

Читает WAV через stdlib `wave`, считает RMS-окна и находит «хук» — самый
энергичный участок, который и станет вертикальным клипом.
"""

from __future__ import annotations

import math
import struct
import wave


def _read_wav_mono(path: str) -> tuple[list[float], int]:
    with wave.open(path, "rb") as wf:
        n_ch = wf.getnchannels()
        sw = wf.getsampwidth()
        sr = wf.getframerate()
        n = wf.getnframes()
        frames = wf.readframes(n)
    if sw == 2:
        count = n * n_ch
        samples = struct.unpack("<" + "h" * count, frames)
        if n_ch == 1:
            mono = [s / 32768.0 for s in samples]
        else:
            mono = []
            for i in range(0, count, n_ch):
                s = sum(samples[i : i + n_ch]) / n_ch
                mono.append(s / 32768.0)
    elif sw == 3:
        mono = []
        step = 3 * n_ch
        for i in range(0, len(frames), step):
            channels = []
            for c in range(n_ch):
                off = i + c * 3
                b = frames[off : off + 3]
                if len(b) < 3:
                    channels.append(0)
                    continue
                val = int.from_bytes(b, "little", signed=True)
                channels.append(val / (1 << 23))
            mono.append(sum(channels) / max(1, n_ch))
    elif sw == 4:
        count = n * n_ch
        samples = struct.unpack("<" + "i" * count, frames)
        norm = float(1 << 31)
        if n_ch == 1:
            mono = [s / norm for s in samples]
        else:
            mono = []
            for i in range(0, count, n_ch):
                s = sum(samples[i : i + n_ch]) / n_ch
                mono.append(s / norm)
    else:
        raise ValueError(f"Unsupported sample width: {sw}")
    return mono, sr


def _rms_windows(samples: list[float], sr: int, win_sec: float = 1.0) -> list[float]:
    win = max(1, int(sr * win_sec))
    out = []
    for i in range(0, len(samples), win):
        chunk = samples[i : i + win]
        if not chunk:
            continue
        s = sum(x * x for x in chunk) / len(chunk)
        out.append(math.sqrt(s))
    return out


def detect_hook(master_wav: str, target_sec: int = 20) -> tuple[float, float]:
    """Возвращает (start_sec, end_sec) для самого «мясного» куска."""
    try:
        samples, sr = _read_wav_mono(master_wav)
    except Exception as e:
        _safe_print(f"[video_edit] hook detect fail: {e}")
        return (0.0, float(target_sec))
    total = len(samples) / sr
    if total <= target_sec + 1:
        return (0.0, total)
    rms = _rms_windows(samples, sr, win_sec=1.0)
    w = target_sec
    if w >= len(rms):
        return (0.0, float(target_sec))
    best_sum = -1.0
    best_start = 0
    running = sum(rms[:w])
    if running > best_sum:
        best_sum, best_start = running, 0
    for i in range(1, len(rms) - w + 1):
        running += rms[i + w - 1] - rms[i - 1]
        if running > best_sum:
            best_sum, best_start = running, i
    # Prefer second half — избегаем интро
    if best_start < 0.25 * len(rms):
        half = len(rms) // 2
        if half + w <= len(rms):
            alt_best = sum(rms[half : half + w])
            alt_start = half
            running = alt_best
            for i in range(half + 1, len(rms) - w + 1):
                running += rms[i + w - 1] - rms[i - 1]
                if running > alt_best:
                    alt_best, alt_start = running, i
            if alt_best >= 0.85 * best_sum:
                best_start = alt_start
    return (float(best_start), float(best_start + w))

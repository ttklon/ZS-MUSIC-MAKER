# -*- coding: utf-8 -*-
"""
modules/beat/drums.py — синтез барабанов как честного FALLBACK.

Сэмпловый банк (`data/samples/`) всегда приоритетнее: живой оne-shot нельзя
заменить. Но когда банка нет, бит не должен звучать «как игрушка из синусов».
Здесь каждый инструмент собран из тех же слоёв, что и в реальной записи:

* kick    — питч-конверт (удар головки) + клик битера + сатурированное тело;
* snare   — две моды корпуса + полосно-ограниченный шум + транзиент;
* clap    — четыре коротких хлопка с разлётом 7–10 мс и «хвост» зала;
* hat     — металлический FM-кластер (6 негармонических прямоугольников),
            закрытый и открытый, плюс шумовая подложка;
* bass808 — синус с глиссандо и мягкой сатурацией, длинный сустейн.

Все функции детерминированы: шум берётся только из переданного генератора,
поэтому seed → идентичный WAV. Никакого `np.random` из глобального состояния.
"""

from __future__ import annotations

from typing import Any

import numpy as np

try:  # scipy есть в базовых требованиях, но модуль не должен падать без него
    from scipy.signal import butter as _butter
    from scipy.signal import sosfilt as _sosfilt

    HAS_SCIPY = True
except Exception:  # pragma: no cover - окружение без scipy
    _butter = None
    _sosfilt = None
    HAS_SCIPY = False


def _sos(kind: str, cutoff: float | tuple[float, float], sr: int, order: int = 2):
    if not HAS_SCIPY:
        return None
    return _butter(order, cutoff, btype=kind, fs=sr, output="sos")


def bandpass(signal: np.ndarray, low: float, high: float, sr: int, order: int = 2) -> np.ndarray:
    """Полосовой фильтр Баттерворта; без scipy — честный no-op (сигнал не рвём)."""
    sos = _sos("bandpass", (max(20.0, low), min(sr / 2 - 100.0, high)), sr, order)
    if sos is None:
        return signal
    return _sosfilt(sos, signal).astype(np.float32)


def highpass(signal: np.ndarray, cutoff: float, sr: int, order: int = 2) -> np.ndarray:
    sos = _sos("highpass", max(20.0, min(cutoff, sr / 2 - 100.0)), sr, order)
    if sos is None:
        return signal
    return _sosfilt(sos, signal).astype(np.float32)


def _peak_normalize(signal: np.ndarray, target: float = 1.0) -> np.ndarray:
    peak = float(np.max(np.abs(signal))) if signal.size else 0.0
    if peak <= 1e-9:
        return signal.astype(np.float32)
    return (signal * (target / peak)).astype(np.float32)


def _soft_clip(signal: np.ndarray, drive: float = 1.6) -> np.ndarray:
    """tanh-сатурация с компенсацией громкости: добавляет гармоники, не ломая пик."""
    if drive <= 0:
        return signal.astype(np.float32)
    return (np.tanh(signal * drive) / np.tanh(drive)).astype(np.float32)


def _noise(rng: Any, size: int) -> np.ndarray:
    if size <= 0:
        return np.zeros(0, dtype=np.float32)
    if rng is None:
        rng = np.random.default_rng(0)
    return np.asarray(rng.standard_normal(size), dtype=np.float32)


def _env(n: int, sr: int, attack: float, tau: float) -> np.ndarray:
    t = np.arange(n, dtype=np.float32) / sr
    decay = np.exp(-t / max(tau, 1e-4))
    rise = np.clip(t / max(attack, 1e-5), 0.0, 1.0)
    return (decay * rise).astype(np.float32)


def synth_kick(
    sr: int,
    rng: Any = None,
    tune: float = 1.0,
    decay: float = 0.24,
    punch: float = 0.42,
    start_hz: float = 165.0,
    end_hz: float = 49.0,
) -> np.ndarray:
    """Панчевый кик: питч-конверт + клик + сатурированное тело."""
    n = int(sr * min(0.8, decay * 2.4))
    if n < 16:
        return np.zeros(max(n, 1), dtype=np.float32)
    t = np.arange(n, dtype=np.float32) / sr
    f_end = end_hz * tune
    f_start = start_hz * tune
    pitch = f_end + (f_start - f_end) * np.exp(-t / 0.028)
    phase = 2.0 * np.pi * np.cumsum(pitch) / sr
    body = np.sin(phase) * _env(n, sr, 0.0015, decay)
    body += 0.13 * np.sin(2.0 * phase) * _env(n, sr, 0.002, decay * 0.45)

    click_n = min(n, int(sr * 0.012))
    click = highpass(_noise(rng, click_n), 2200.0, sr) * _env(click_n, sr, 1e-4, 0.0016)
    beater = np.sin(2.0 * np.pi * 1180.0 * t[:click_n]) * _env(click_n, sr, 1e-4, 0.0035)
    transient = (click * 0.62 + beater * 0.34) * punch
    body[:click_n] += transient

    return _peak_normalize(_soft_clip(body, 1.5))


def synth_snare(
    sr: int,
    rng: Any = None,
    tune: float = 1.0,
    decay: float = 0.16,
    tone_mix: float = 0.45,
    bright: float = 1.0,
) -> np.ndarray:
    """Снейр: две моды корпуса (≈185/330 Гц) + шум 1.4–11 кГц + транзиент."""
    n = int(sr * max(0.18, decay * 2.2))
    t = np.arange(n, dtype=np.float32) / sr
    body = (
        0.62 * np.sin(2.0 * np.pi * 185.0 * tune * t) * _env(n, sr, 0.001, 0.055)
        + 0.38 * np.sin(2.0 * np.pi * 330.0 * tune * t) * _env(n, sr, 0.001, 0.038)
    )
    noise = bandpass(
        _noise(rng, n), 1400.0, min(11000.0 * bright, sr / 2 - 200.0), sr, order=2
    ) * _env(n, sr, 0.0008, decay)
    mix = tone_mix * _peak_normalize(body) + (1.0 - tone_mix) * _peak_normalize(noise)

    click_n = min(n, int(sr * 0.008))
    mix[:click_n] += (
        bandpass(_noise(rng, click_n), 3000.0, min(12000.0, sr / 2 - 200.0), sr)
        * _env(click_n, sr, 1e-4, 0.0012)
        * 0.35
    )
    return _peak_normalize(_soft_clip(mix, 1.3))


def synth_clap(sr: int, rng: Any = None, decay: float = 0.13) -> np.ndarray:
    """Клэп: четыре хлопка с разлётом и общий «хвост» помещения."""
    n = int(sr * max(0.22, decay * 2.4))
    out = np.zeros(n, dtype=np.float32)
    base = bandpass(_noise(rng, n), 900.0, 3600.0, sr, order=2)
    for index, offset_ms in enumerate((0.0, 7.0, 14.0, 22.0)):
        start = int(sr * offset_ms / 1000.0)
        if start >= n:
            break
        seg_len = n - start
        burst_env = _env(seg_len, sr, 2e-4, 0.006 if index < 3 else 0.012)
        out[start:] += base[:seg_len] * burst_env * (0.9 if index < 3 else 0.7)
    tail = base * _env(n, sr, 0.002, decay) * 0.55
    return _peak_normalize(out + tail)


def synth_hat(
    sr: int,
    rng: Any = None,
    open_hat: bool = False,
    tune: float = 1.0,
    metallic: float = 0.72,
) -> np.ndarray:
    """Хэт 808-типа: кластер прямоугольников + шум, ФВЧ 7 кГц."""
    tau = 0.235 if open_hat else 0.042
    n = int(sr * (tau * 5.0 + 0.01))
    t = np.arange(n, dtype=np.float32) / sr
    ratios = (205.3, 304.4, 369.6, 522.7, 540.0, 800.0)
    metal = np.zeros(n, dtype=np.float32)
    for ratio in ratios:
        metal += np.sign(np.sin(2.0 * np.pi * ratio * tune * t))
    metal = highpass(metal / len(ratios), 6800.0, sr, order=3)
    air = highpass(_noise(rng, n), 8200.0, sr, order=3)
    mix = metallic * _peak_normalize(metal) + (1.0 - metallic) * _peak_normalize(air)
    return _peak_normalize(mix * _env(n, sr, 3e-4, tau))


def synth_808(
    sr: int,
    freq: float,
    duration: float,
    rng: Any = None,
    glide: float = 0.030,
    drive: float = 1.9,
) -> np.ndarray:
    """808-бас: синус с небольшим глиссандо, сатурацией и длинным сустейном."""
    n = max(16, int(sr * duration))
    t = np.arange(n, dtype=np.float32) / sr
    start_f = freq * 1.6
    pitch = freq + (start_f - freq) * np.exp(-t / max(glide, 1e-3))
    phase = 2.0 * np.pi * np.cumsum(pitch) / sr
    body = np.sin(phase) + 0.16 * np.sin(2.0 * phase)
    attack = np.clip(t / 0.006, 0.0, 1.0)
    release = np.clip((duration - t) / 0.045, 0.0, 1.0)
    glide_env = 0.82 + 0.18 * np.exp(-t / 0.25)
    return _peak_normalize(_soft_clip(body * attack * release * glide_env, drive))


def synth_sub_impact(sr: int, rng: Any = None, duration: float = 1.1) -> np.ndarray:
    """Импакт дропа: низкий свеп + короткий шумовой «удар» (контраст низа ≥ 6 дБ)."""
    n = max(16, int(sr * duration))
    t = np.arange(n, dtype=np.float32) / sr
    pitch = 36.0 + 74.0 * np.exp(-t / 0.09)
    phase = 2.0 * np.pi * np.cumsum(pitch) / sr
    body = np.sin(phase) * _env(n, sr, 0.003, duration * 0.42)
    thump_n = min(n, int(sr * 0.05))
    thump = highpass(_noise(rng, thump_n), 1600.0, sr) * _env(thump_n, sr, 2e-4, 0.012)
    body[:thump_n] += thump * 0.5
    return _peak_normalize(_soft_clip(body, 1.2))


# Баланс микса для FALLBACK-синтеза: каждый one-shot нормирован в 1.0, но в
# миксе кик и бас не должны «съедать» хэты и малый. Значения подобраны по
# измерениям (RMS/центроид/крест) на 15-секундном рендере.
INSTRUMENT_GAIN = {
    "kick": 0.58,
    "snare": 0.46,
    "clap": 0.32,
    "hat": 0.28,
    "bass808": 0.34,
    "impact": 0.38,
}


CAPABILITIES = {
    "engine": "procedural_drum_synth",
    "status": "FALLBACK",
    "reason": "sample bank is empty; synthesised one-shots are used instead",
    "instruments": ("kick", "snare", "clap", "hat", "bass808", "impact"),
    "scipy": HAS_SCIPY,
}


if __name__ == "__main__":  # pragma: no cover - ручная проверка
    import soundfile as sf

    sr = 44100
    rng = np.random.default_rng(7)
    voices = [
        synth_kick(sr, rng),
        synth_snare(sr, rng),
        synth_clap(sr, rng),
        synth_hat(sr, rng),
        synth_hat(sr, rng, open_hat=True),
        synth_808(sr, 55.0, 0.5, rng),
    ]
    gap = np.zeros(int(sr * 0.05), dtype=np.float32)
    track = np.concatenate([np.concatenate([v, gap]) for v in voices])
    sf.write("/tmp/drum_kit.wav", track, sr)
    print(f"drum self-test: {len(voices)} instruments -> /tmp/drum_kit.wav")

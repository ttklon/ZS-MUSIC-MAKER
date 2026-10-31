# -*- coding: utf-8 -*-
"""
modules/anti_neuro_track.py — «оживление» финального микса перед мастерингом.

Пост-обработка трека: микро-джиттер тайминга, дыхания из `voice_vault`,
динамика по секциям, вычитание ghost-гармоник, разрушение формульного
8-барного цикла, лента, несовершенный тюн, lofi-срез верхов.

Все эффекты детерминированы по `seed`. Без numpy/soundfile —
`polish_track` возвращает `{"ok": False, "error": "soundfile unavailable"}`,
а не молчаливый успех.
"""

from __future__ import annotations

import math
import random
import time
from pathlib import Path

try:
    import numpy as _np
    import soundfile as _sf

    NP_OK = True
except Exception:  # noqa: BLE001
    _np = None
    _sf = None
    NP_OK = False


# --------------------------------------------------------------------------- #
#  Трек-уровень: пост-обработка финального микса/мастера
# --------------------------------------------------------------------------- #
# Цепочка «оживления» перед мастерингом: микро-джиттер тайминга, дыхания из
# voice_vault, динамика по секциям, вычитание ghost-гармоник, разрушение
# формульного 8-барного цикла, лента, несовершенный тюн, lofi-срез верхов.

# ============================================================ IO
def _read_track(path: str):
    if not NP_OK:
        return None, None
    y, sr = _sf.read(path, always_2d=True)
    return y, sr


def _write_track(path: str, y, sr):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    _sf.write(path, y, sr)


# ============================================================ effects
def _micro_timing_jitter(y, sr, amount_ms: float = 5.0, seed: int | None = None):
    if np is None:
        return y
    rng = _np.random.default_rng(seed or int(time.time()))
    seg_len = int(sr * 0.5)  # 500 мс блоки
    max_shift = int(sr * amount_ms / 1000.0)
    if max_shift <= 0:
        return y
    out = _np.zeros_like(y)
    pos = 0
    while pos < len(y):
        seg = y[pos : pos + seg_len]
        shift = int(rng.integers(-max_shift, max_shift + 1))
        start = max(0, pos + shift)
        end = min(len(out), start + len(seg))
        out[start:end] += seg[: end - start] * 0.98
        pos += seg_len
    peak = float(_np.max(_np.abs(out))) or 1.0
    if peak > 0.99:
        out = out * (0.99 / peak)
    return out


def _breath_insert(
    y, sr, breath_samples: list, positions_sec: list, volume_db: float = -22.0
):
    if np is None or not breath_samples:
        return y
    out = y.copy()
    gain = 10 ** (volume_db / 20.0)
    for t in positions_sec:
        idx = int(t * sr)
        if idx >= len(out):
            continue
        br = breath_samples[hash(t) % len(breath_samples)]
        if br is None:
            continue
        L = min(len(br), len(out) - idx)
        if out.ndim == 2 and br.ndim == 1:
            out[idx : idx + L, 0] += br[:L] * gain
            if out.shape[1] > 1:
                out[idx : idx + L, 1] += br[:L] * gain * 0.9
        else:
            out[idx : idx + L] += br[:L] * gain
    return out


def _section_dynamics_variation(y, sr, sections: list, seed: int | None = None):
    if np is None or not sections:
        return y
    rng = random.Random(seed or int(time.time()))
    out = y.copy()
    for sec in sections:
        s = int(sec.get("start_sec", 0.0) * sr)
        e = int(sec.get("end_sec", 0.0) * sr)
        if e <= s or s >= len(out):
            continue
        e = min(e, len(out))
        energy = float(sec.get("energy", 0.7))
        span_db = 1.5 if energy < 0.5 else 0.7
        gain_db = rng.uniform(-span_db, span_db)
        gain = 10 ** (gain_db / 20.0)
        out[s:e] = out[s:e] * gain
    peak = float(_np.max(_np.abs(out))) or 1.0
    if peak > 0.99:
        out = out * (0.99 / peak)
    return out


def _ghost_harmonies_kill(y, sr):
    """
    Устранение "призрачных" гармоник, типичных для RVC/нейронок.
    v14: Добавлены адаптивные частоты 3.2k, 4.8k, 6.4k, 8k.
    """
    if np is None:
        return y
    try:
        import scipy.signal as sg
    except Exception:
        return y
    out = y.copy()
    # Нейронки часто свистят на кратных частотах
    for freq in (3200.0, 4800.0, 6400.0, 8000.0):
        if freq >= sr / 2:
            continue
        b, a = sg.iirnotch(w0=freq / (sr / 2), Q=35.0)  # Узкий notch
        if out.ndim == 2:
            for ch in range(out.shape[1]):
                out[:, ch] = sg.filtfilt(b, a, out[:, ch])
        else:
            out = sg.filtfilt(b, a, out)
    return out


def _formulaic_structure_bust(y, sr, seed: int | None = None):
    if np is None:
        return y
    rng = random.Random(seed or int(time.time()))
    dur = len(y) / sr
    if dur < 30:
        return y
    out = y.copy()
    n_drops = rng.randint(1, 2)
    for _ in range(n_drops):
        t = rng.uniform(0.3 * dur, 0.85 * dur)
        drop_len = rng.uniform(0.05, 0.12)
        s = int(t * sr)
        e = int((t + drop_len) * sr)
        e = min(e, len(out))
        if e <= s:
            continue
        out[s:e] *= rng.uniform(0.05, 0.20)
    return out


def _tape_saturation(y, amount: float = 0.06):
    if np is None:
        return y
    x = _np.clip(y * (1 + amount), -1.0, 1.0)
    return _np.tanh(x * (1 + amount)) * (1 / (1 + amount))


def _imperfect_tuning(y, sr, cents: float = 4.0):
    """
    Реальное микро-расстроение (vibrato) через интерполяцию.
    """
    if np is None:
        return y
    try:
        from scipy.interpolate import interp1d
    except Exception:
        return y

    # LFO для сдвига фазы (времени)
    # 0.3 Hz - медленное плавание
    t = _np.arange(len(y)) / sr
    # cents to frequency ratio: f_new = f_old * 2^(cents/1200)
    # Мы имитируем это через модуляцию времени
    lfo = _np.sin(2 * math.pi * 0.3 * t) * (cents / 1200.0)

    # Искажаем временную шкалу
    time_indices = _np.arange(len(y))
    # Интегрируем изменение частоты для получения изменения фазы/времени
    # Но для малых отклонений можно просто добавить LFO к индексам
    modulated_indices = time_indices + lfo * 10.0  # небольшой джиттер

    if y.ndim == 2:
        out = _np.zeros_like(y)
        for ch in range(y.shape[1]):
            f = interp1d(
                time_indices, y[:, ch], kind="linear", fill_value="extrapolate"
            )
            out[:, ch] = f(modulated_indices)
        return out
    else:
        f = interp1d(time_indices, y, kind="linear", fill_value="extrapolate")
        return f(modulated_indices)


def _lofi_pass(y, sr, cutoff: float = 15000.0):
    if np is None:
        return y
    try:
        import scipy.signal as sg
    except Exception:
        return y
    b, a = sg.butter(4, cutoff / (sr / 2), btype="low")
    if y.ndim == 2:
        out = y.copy()
        for ch in range(y.shape[1]):
            out[:, ch] = sg.filtfilt(b, a, y[:, ch])
        return out
    return sg.filtfilt(b, a, y)


# ============================================================ main API
def polish_track(
    input_wav: str,
    output_wav: str,
    arrangement_plan: dict | None = None,
    breath_samples: list | None = None,
    preset: str = "standard",
    seed: int | None = None,
) -> dict:
    """
    preset:
      • gentle    — минимальная обработка (для sing/melodic)
      • standard  — универсал (default)
      • aggressive — жёсткое разрушение формульности (для phonk / trap)
    """
    if not NP_OK:
        return {"ok": False, "error": "soundfile unavailable"}
    y, sr = _read_track(input_wav)
    if y is None:
        return {"ok": False, "error": f"cannot read {input_wav}"}

    stages_applied = []

    amount_ms = {"gentle": 2.5, "standard": 5.0, "aggressive": 8.0}[preset]
    y = _micro_timing_jitter(y, sr, amount_ms=amount_ms, seed=seed)
    stages_applied.append(f"micro_timing_jitter({amount_ms}ms)")

    if breath_samples and arrangement_plan:
        secs = arrangement_plan.get("sections", [])
        positions = []
        for s in secs:
            if s.get("name", "").startswith(("verse", "chorus", "prechorus")):
                positions.append(float(s.get("start_sec", 0.0)) + 0.05)
        y = _breath_insert(y, sr, breath_samples, positions, volume_db=-24.0)
        stages_applied.append(f"breath_insert(n={len(positions)})")

    if arrangement_plan and arrangement_plan.get("sections"):
        y = _section_dynamics_variation(y, sr, arrangement_plan["sections"], seed=seed)
        stages_applied.append("section_dynamics_variation")

    if preset in ("standard", "aggressive"):
        y = _ghost_harmonies_kill(y, sr)
        stages_applied.append("ghost_harmonies_kill")

    if preset == "aggressive":
        y = _formulaic_structure_bust(y, sr, seed=seed)
        stages_applied.append("formulaic_structure_bust")

    y = _tape_saturation(
        y, amount={"gentle": 0.02, "standard": 0.05, "aggressive": 0.09}[preset]
    )
    stages_applied.append("tape_saturation")

    if preset in ("gentle", "standard"):
        y = _imperfect_tuning(y, sr, cents=3.0)
        stages_applied.append("imperfect_tuning")

    cutoff = {"gentle": 17000.0, "standard": 16000.0, "aggressive": 14500.0}[preset]
    y = _lofi_pass(y, sr, cutoff=cutoff)
    stages_applied.append(f"lofi_pass({cutoff:.0f})")

    _write_track(output_wav, y, sr)
    return {
        "ok": True,
        "input": input_wav,
        "output": output_wav,
        "preset": preset,
        "stages_applied": stages_applied,
        "sr": int(sr),
    }

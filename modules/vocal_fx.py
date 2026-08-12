# -*- coding: utf-8 -*-
"""
ZS Music Maker v18 — modules/vocal_fx.py (vocal double + delay throw, TZ 4.x)
================================================================================

Назначение: дать вокалу «хитовую» плотность БЕЗ нейросетей и платных API —
классический студийный приём double-tracking + delay throw на конце фраз.

Два эффекта, оба честные DSP (не имитация):

  1) double  — «второй дабл»: вокал слегка растягивается по времени
     (±0.6 %) и детюнится (±8 центов), микшируется тихо под основной.
     Это имитирует живой второй дубль (именно так делают «толстый» хук
     на реальных записях), а НЕ выдаётся за RVC/нейросеть.
  2) throw   — ping-pong delay throw: на конце фразы (по VAD-тишине)
     появляется эхо-бросок, который заполняет паузу перед хуком.
     Даёт драматургию и современное звучание.

Честные ограничения:
  — работает только на numpy + soundfile (без scipy/torch/audiocraft);
  — если soundfile недоступен -> ok=False, reason (НЕ молчаливый copy);
  — параметры консервативны, чтобы не превратить вокал в «плывущий» сигнал.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as _np
    import soundfile as _sf
    _OK = True
except Exception:
    _np = None
    _sf = None
    _OK = False


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _read(wav_path: str) -> Tuple[Any, int]:
    y, sr = _sf.read(wav_path, always_2d=True)
    return y.astype("float32"), int(sr)


def _write(wav_path: str, y, sr: int) -> str:
    Path(wav_path).parent.mkdir(parents=True, exist_ok=True)
    _sf.write(wav_path, _np.clip(y, -1.0, 1.0), sr)
    return wav_path


def _resample_linear(y, factor: float):
    """Честный линейный ресемпл по времени (без scipy).

    factor > 1 — сигнал короче/выше; < 1 — длиннее/ниже.
    Используется для микро-растяжения дабла (0.994–1.006), где
    линейная интерполяция не даёт слышимых артефактов.
    """
    n = len(y)
    if n < 2:
        return y
    new_n = max(2, int(round(n / factor)))
    x_old = _np.linspace(0.0, 1.0, n)
    x_new = _np.linspace(0.0, 1.0, new_n)
    if y.ndim == 1:
        return _np.interp(x_new, x_old, y).astype("float32")
    out = _np.empty((new_n, y.shape[1]), dtype="float32")
    for c in range(y.shape[1]):
        out[:, c] = _np.interp(x_new, x_old, y[:, c])
    return out


def _detune_cents(y, sr: int, cents: float):
    """Детюн в центах через ресемпл (честный pitch+time shift)."""
    factor = 2.0 ** (cents / 1200.0)
    return _resample_linear(y, factor)


def _fit_len(y, n: int):
    if len(y) == n:
        return y
    if len(y) > n:
        return y[:n]
    pad = _np.zeros((n - len(y),) + y.shape[1:], dtype=y.dtype)
    return _np.concatenate([y, pad], axis=0)


def _rms_db(x) -> float:
    r = float(_np.sqrt(_np.mean(x ** 2)) + 1e-9)
    return 20.0 * math.log10(r)


def _find_phrase_ends(mono, sr: int,
                      silence_db: float = -40.0,
                      min_silence_ms: int = 180) -> List[int]:
    """Грубый VAD: ищем концы фраз = начало длинной паузы.

    Возвращает список sample-индексов, где фраза заканчивается
    (за ними идёт тишина). На них вешаем delay throw.
    """
    frame = max(1, int(sr * 0.02))          # 20 ms окно
    hop = frame
    n_fr = max(1, len(mono) // hop)
    rms = _np.empty(n_fr, dtype="float32")
    for i in range(n_fr):
        seg = mono[i * hop:(i + 1) * hop]
        rms[i] = float(_np.sqrt(_np.mean(seg ** 2)) + 1e-9)
    thr = 10.0 ** (silence_db / 20.0)
    voiced = rms > thr
    min_sil_frames = max(1, int(min_silence_ms / 20.0))
    ends: List[int] = []
    i = 0
    while i < n_fr:
        if voiced[i]:
            # ищем конец voiced-участка
            j = i
            while j < n_fr and voiced[j]:
                j += 1
            # j — первый тихий фрейм; если тишина длинная — это конец фразы
            k = j
            while k < n_fr and not voiced[k]:
                k += 1
            if (k - j) >= min_sil_frames and j > 0:
                ends.append(j * hop)
            i = k
        else:
            i += 1
    return ends


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

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
    reason: Optional[str] = None


def apply_vocal_double(vocal_wav: str,
                       out_wav: str,
                       double_level_db: float = -10.0,
                       detune_cents: float = 8.0,
                       time_stretch: float = 0.006,
                       pre_delay_ms: float = 22.0) -> VocalFxResult:
    """Классический double-tracking: детюн+микро-растянутый дабл под основой."""
    if not _OK:
        return VocalFxResult(False, "", "none", False, False, 0,
                             -100.0, -100.0,
                             reason="numpy/soundfile unavailable")
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
            True, out_wav, "numpy_double_tracking",
            double_used=True, throw_used=False, throws_applied=0,
            in_rms_db=_rms_db(y), out_rms_db=_rms_db(out))
    except Exception as e:
        return VocalFxResult(False, "", "none", False, False, 0,
                             -100.0, -100.0, reason=str(e))


def apply_delay_throw(vocal_wav: str,
                      out_wav: str,
                      delay_ms: float = 320.0,
                      feedback: float = 0.32,
                      throw_level_db: float = -9.0,
                      silence_db: float = -40.0,
                      ping_pong: bool = True) -> VocalFxResult:
    """Delay throw: эхо-бросок в паузах на концах фраз (заполняет воздух)."""
    if not _OK:
        return VocalFxResult(False, "", "none", False, False, 0,
                             -100.0, -100.0,
                             reason="numpy/soundfile unavailable")
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
                    wet[pos:pos + room] += seg2[:room]
                else:
                    wet[pos:pos + room] += seg[:room]
                pos += d
                level *= feedback
                taps += 1

        out = y + wet
        peak = float(_np.max(_np.abs(out)) + 1e-9)
        if peak > 1.0:
            out = out / peak * 0.98
        _write(out_wav, out, sr)
        return VocalFxResult(
            True, out_wav, "numpy_delay_throw",
            double_used=False, throw_used=True, throws_applied=throws,
            in_rms_db=_rms_db(y), out_rms_db=_rms_db(out))
    except Exception as e:
        return VocalFxResult(False, "", "none", False, False, 0,
                             -100.0, -100.0, reason=str(e))


def process_vocal(vocal_wav: str,
                  out_wav: str,
                  use_double: bool = True,
                  use_throw: bool = True,
                  double_level_db: float = -10.0,
                  throw_level_db: float = -9.0,
                  delay_ms: float = 320.0) -> Dict[str, Any]:
    """Единая точка: double -> throw -> out. Возвращает dict-результат."""
    if not _OK:
        return {"ok": False, "engine": "none",
                "reason": "numpy/soundfile unavailable"}

    cur = vocal_wav
    stages: List[str] = []
    throws = 0
    tmp_double = str(Path(out_wav).with_name("_fx_double_tmp.wav"))

    if use_double:
        r = apply_vocal_double(cur, tmp_double,
                               double_level_db=double_level_db)
        if r.ok:
            cur = tmp_double
            stages.append("double")

    if use_throw:
        r = apply_delay_throw(cur, out_wav, delay_ms=delay_ms,
                              throw_level_db=throw_level_db)
        if r.ok:
            cur = out_wav
            stages.append("throw")
            throws = r.throws_applied
        else:
            # throw не критичен — остаёмся на double
            try:
                import shutil
                shutil.copy(cur, out_wav)
                cur = out_wav
            except Exception:
                pass

    if not stages:
        # оба не сработали — честно сообщаем, не делаем скрытый copy
        return {"ok": False, "engine": "none",
                "reason": "double and throw both failed"}

    # подчистить временный файл
    try:
        p = Path(tmp_double)
        if p.exists() and cur != tmp_double:
            p.unlink()
    except Exception:
        pass

    return {
        "ok": True,
        "engine": "numpy_vocal_fx",
        "path": cur,
        "out_wav": cur,
        "stages": stages,
        "throws_applied": throws,
        "double_used": "double" in stages,
        "throw_used": "throw" in stages,
    }


def capability_report() -> Dict[str, Any]:
    return {"numpy_soundfile": _OK, "real_double_possible": _OK,
            "real_throw_possible": _OK}


if __name__ == "__main__":
    print(json.dumps(capability_report(), indent=2))

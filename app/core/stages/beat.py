# -*- coding: utf-8 -*-
"""
app/core/stages/beat.py — Бит: вызов `beat_constructor` и честный процедурный синтез-фоллбек.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# `_arrangement_drives_beat` реэкспортируется: его проверяют тесты и отчёты
# через этот модуль, а живёт он рядом с разбором плана.
from app.core.stages.beat_arrangement import (  # noqa: F401
    _arrangement_drives_beat,
    _arrangement_sections,
)

def _stage_ai_beat(recipe: dict[str, Any], plan: Any, out_dir: Path,
                   style: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    """Explicit external model: no substitution if it is missing or fails."""
    expected = recipe.get("recorded_backing_sha256", "")
    if expected and recipe.get("beat_engine") != "user_audio":
        return {"ok": False, "engine": "user_instrumental", "reason": "recorded backing required; select the original or record again"}
    if recipe.get("beat_engine") == "user_audio":
        try:
            from app.core.stages.imported_beat import import_instrumental
            return import_instrumental(recipe.get("beat_input_path", ""), out_dir / "beat.wav", expected_sha256=expected)
        except Exception as exc:
            prefix = "recorded backing: " if expected else ""
            return {"ok": False, "engine": "user_instrumental", "reason": f"{prefix}{type(exc).__name__}: {exc}"}
    if recipe.get("beat_engine") != "ace_step":
        return {"ok": False, "reason": f"unknown beat engine: {recipe.get('beat_engine')}"}
    if dry_run:
        return {"ok": True, "blocked": True, "reason": "ACE-Step skipped in dry run"}
    try:
        import os
        from app.ai.acestep import generate_instrumental

        prompt = f"Instrumental {recipe['genre']}, {recipe['theme']}; no vocals"
        return generate_instrumental(
            prompt, out_dir / "beat.wav", duration_sec=float((plan or {}).get("duration_sec") or 90),
            bpm=int(style.get("target_bpm") or 128), key=recipe_key(style), seed=recipe.get("seed"),
            base_url=os.getenv("ZSMM_ACESTEP_URL", "http://127.0.0.1:8001"),
            timeout_sec=float(os.getenv("ZSMM_ACESTEP_TIMEOUT", "7200")),
        )
    except Exception as exc:
        return {"ok": False, "engine": "ace_step_1_5_api", "reason": f"{type(exc).__name__}: {exc}"}


def _stage_beat(
    plan: Any,
    out_dir: Path,
    groove: Any = None,
    style_vector: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """v17 FIX (P0): construct_beat вместо несуществующего build_beat."""
    beat_wav = str(out_dir / "beat.wav")
    try:
        from modules import beat_constructor as bc

        style = style_vector or {"target_bpm": 128, "target_mode": "minor"}
        sections, arrangement_note = _arrangement_sections(plan)
        if hasattr(bc, "construct_beat"):
            r = bc.construct_beat(
                groove or {},
                [],
                style,
                duration_sec=int((plan or {}).get("duration_sec", 90)),
                n_verses=int((plan or {}).get("n_verses", 2)),
                aggression=float((plan or {}).get("aggression", 0.7)),
                out_name=Path(beat_wav).name,
                sections=sections,
            )
            if isinstance(r, dict) and r.get("beat_path"):
                src = Path(r["beat_path"])
                dst = Path(beat_wav)
                if src.exists() and src.resolve() != dst.resolve():
                    try:
                        import shutil

                        shutil.copy(src, dst)
                    except Exception:
                        dst = src
                return {
                    "ok": True,
                    "path": str(dst),
                    "bpm": r.get("bpm"),
                    "key": r.get("key"),
                    "sections": r.get("sections"),
                    "duration_sec": r.get("duration_sec"),
                    "engine": "beat_constructor.construct_beat",
                    "arrangement_driven": bool(sections),
                    **({"arrangement_note": arrangement_note} if arrangement_note else {}),
                }
        # v22: fallback — полный structured synth beat, не 8с тупые kicks
        _bpm = int(style.get("target_bpm", 128) or 128)
        _dur = int((plan or {}).get("duration_sec", 90) or 90)
        _key = recipe_key(style)
        return _synth_beat(
            beat_wav, duration=_dur, bpm=_bpm, key_root=_key.split()[0], key_name=_key
        )
    except Exception as e:
        try:
            _bpm = int((style_vector or {}).get("target_bpm", 128))
            _dur = int((plan or {}).get("duration_sec", 90))
            _key = recipe_key(style_vector)
            return _synth_beat(
                beat_wav, duration=_dur, bpm=_bpm, key_root=_key.split()[0], key_name=_key
            )
        except Exception:
            return {"ok": False, "reason": str(e)}


def recipe_key(style: dict[str, Any] | None) -> str:
    """Тональность из style_vector («A minor»), по умолчанию A minor."""
    style = style or {}
    root = str(style.get("key_root") or "A").upper()
    mode = str(style.get("target_mode") or "minor").lower()
    if mode not in ("major", "minor"):
        mode = "minor"
    return f"{root} {mode}"


def _synth_beat(
    out_wav: str,
    duration: int = 90,
    bpm: int = 128,
    key_root: str = "A",
    key_name: str | None = None,
) -> dict[str, Any]:
    """v22: полноценный structured synth-бит (не 8 сек тупых киков).
    Многосекционная структура (intro/verse/pre/chorus/verse/pre/chorus/outro),
    808 sub-bass по ключу, hi-hat roll перед drop, snare с air-tail,
    open-hat на offbeat, stop-time перед хуком, white+sub ризеры.
    Честно помечаем fallback_used=True — не выдаём за real beat_constructor.
    """
    try:
        import numpy as np
        import soundfile as sf

        sr = 44100
        beat_sec = 60.0 / bpm
        bar_sec = beat_sec * 4
        step_sec = bar_sec / 16.0

        keys = {
            "C": 261.63,
            "C#": 277.18,
            "D": 293.66,
            "D#": 311.13,
            "E": 329.63,
            "F": 349.23,
            "F#": 369.99,
            "G": 392.00,
            "G#": 415.30,
            "A": 440.00,
            "A#": 466.16,
            "B": 493.88,
        }
        root_hz = keys.get(key_root.upper(), 440.0) / 4.0

        sections = [
            ("intro", 4),
            ("verse", 8),
            ("pre", 4),
            ("chorus", 8),
            ("verse", 8),
            ("pre", 4),
            ("chorus", 8),
            ("outro", 4),
        ]
        total_bars = sum(nb for _, nb in sections)
        target_bars = max(4, int(round(duration / bar_sec)))
        if target_bars < total_bars:
            scale = target_bars / float(total_bars)
            sections = [(nm, max(1, int(round(nb * scale)))) for nm, nb in sections]
        elif target_bars > total_bars * 1.4:
            extra = target_bars - total_bars
            sections = [
                (nm, nb + (extra // 2 if nm == "chorus" else 0)) for nm, nb in sections
            ]

        total_samples = int(sum(nb * bar_sec for _, nb in sections) * sr)
        y = np.zeros(total_samples, dtype="float32")

        kick_pat = [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0]
        snare_pat = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
        hihat_pat = [1] * 16
        openhat_step = 10
        # v25 (P1): секционная вариативность — припев ритмически плотнее
        # куплета (было: одинаковый 16-шаговый шаблон везде, отличие только
        # в гейнах → скучный «формульный» бит, mode hit_scorer 'needs_work').
        # chorus: больше киков (syncopation), verse: разряженнее.
        kick_pat_chorus = [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0]
        kick_pat_verse = [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        hihat_pat_chorus = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        hihat_pat_verse = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0]

        def _kick(sr_, dur=0.16):
            t = np.arange(int(sr_ * dur)) / sr_
            f = 90.0 * np.exp(-t * 18) + 45.0
            env = np.exp(-t * 11)
            body = np.sin(2 * np.pi * np.cumsum(f) / sr_) * env
            click = (
                np.random.randn(int(sr_ * 0.004)).astype("float32")
                * np.exp(-np.arange(int(sr_ * 0.004)) / sr_ * 400)
                * 0.6
            )
            out = body.astype("float32")
            out[: len(click)] += click * 0.35
            return out

        def _snare(sr_, dur=0.18):
            t = np.arange(int(sr_ * dur)) / sr_
            env = np.exp(-t * 17)
            noise = np.random.randn(len(t)).astype("float32")
            body = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 30)
            air = np.concatenate([[0], np.diff(noise)])
            return (body * 0.35 + air * 0.75) * env * 0.75

        def _hat(sr_, dur=0.045, open_=False):
            t = np.arange(int(sr_ * dur)) / sr_
            env = np.exp(-t * (30 if open_ else 90))
            noise = np.random.randn(len(t)).astype("float32")
            hp = np.concatenate([[0], np.diff(noise)])
            return hp * env * (0.5 if open_ else 0.32)

        def _808(sr_, dur, freq):
            t = np.arange(int(sr_ * dur)) / sr_
            env = np.exp(-t * 2.2) * (1.0 - np.exp(-t * 80.0))
            f = freq * (1.0 + 0.03 * np.exp(-t * 20))
            osc = np.sin(2 * np.pi * np.cumsum(f) / sr_)
            return np.tanh(osc * 1.6) * env * 0.85

        def _riser(sr_, dur, kind="white"):
            t = np.arange(int(sr_ * dur)) / sr_
            if kind == "white":
                env = (t / dur) ** 1.3
                n = np.random.randn(len(t)).astype("float32")
                n = np.concatenate([[0], np.diff(n)])
                return n * env * 0.35
            env = (t / dur) ** 1.6
            f = 80.0 + 800.0 * (t / dur) ** 2
            return np.sin(2 * np.pi * np.cumsum(f) / sr_).astype("float32") * env * 0.5

        pos = 0
        section_info = []
        for section_name, n_bars in sections:
            sec_start_sec = pos / sr
            sec_len = int(n_bars * bar_sec * sr)
            if section_name == "intro":
                kick_gain, snare_gain, hat_gain, bass_gain = 0.55, 0.0, 0.35, 0.4
            elif section_name == "verse":
                kick_gain, snare_gain, hat_gain, bass_gain = 0.9, 0.75, 0.7, 0.85
            elif section_name == "pre":
                kick_gain, snare_gain, hat_gain, bass_gain = 0.85, 0.7, 0.9, 0.8
            elif section_name == "chorus":
                kick_gain, snare_gain, hat_gain, bass_gain = 1.0, 0.95, 0.75, 1.0
            else:  # outro
                kick_gain, snare_gain, hat_gain, bass_gain = 0.7, 0.4, 0.5, 0.5

            # v25: выбор паттернов по секции (вариативность)
            if section_name == "chorus":
                _kp, _hp = kick_pat_chorus, hihat_pat_chorus
            elif section_name == "verse":
                _kp, _hp = kick_pat_verse, hihat_pat_verse
            else:
                _kp, _hp = kick_pat, hihat_pat

            for bar in range(n_bars):
                bar_pos = pos + bar * int(bar_sec * sr)
                for step in range(16):
                    step_pos = bar_pos + int(step * step_sec * sr)
                    if _kp[step] and section_name != "intro":
                        k = _kick(sr) * kick_gain
                        e = min(step_pos + len(k), total_samples)
                        y[step_pos:e] += k[: e - step_pos]
                    if snare_pat[step] and section_name != "intro":
                        s_ = _snare(sr) * snare_gain
                        e = min(step_pos + len(s_), total_samples)
                        y[step_pos:e] += s_[: e - step_pos]
                    if _hp[step]:
                        is_open = step == openhat_step and section_name != "intro"
                        h = _hat(sr, open_=is_open) * hat_gain
                        e = min(step_pos + len(h), total_samples)
                        y[step_pos:e] += h[: e - step_pos]
                    if _kp[step] and section_name != "intro":
                        b_dur = beat_sec * 1.5
                        b = _808(sr, b_dur, root_hz) * bass_gain
                        e = min(step_pos + len(b), total_samples)
                        y[step_pos:e] += b[: e - step_pos] * 0.65

                # Снейр-ролл в последнем баре pre-chorus
                if section_name == "pre" and bar == n_bars - 1:
                    roll_start = bar_pos + int(2 * beat_sec * sr)
                    n_hits = 8
                    hit_sec = (2 * beat_sec) / n_hits
                    for h_i in range(n_hits):
                        hp = roll_start + int(h_i * hit_sec * sr)
                        s_ = _snare(sr, dur=0.09) * (0.4 + 0.06 * h_i)
                        e = min(hp + len(s_), total_samples)
                        y[hp:e] += s_[: e - hp]
                    ris_dur = 2 * beat_sec
                    wr = _riser(sr, ris_dur, "white")
                    e = min(roll_start + len(wr), total_samples)
                    y[roll_start:e] += wr[: e - roll_start]
                    sr_ = _riser(sr, ris_dur, "sub")
                    e = min(roll_start + len(sr_), total_samples)
                    y[roll_start:e] += sr_[: e - roll_start]

            # Стоп-тайм перед хуком: последние 2 шага pre — приглушить
            if section_name == "pre":
                cut = int(step_sec * 2 * sr)
                if sec_len > cut:
                    y[pos + sec_len - cut : pos + sec_len] *= 0.15

            pos += sec_len
            section_info.append(
                {
                    "name": section_name,
                    "bars": n_bars,
                    "start_sec": round(sec_start_sec, 2),
                    "duration_sec": round(n_bars * bar_sec, 2),
                }
            )

        # v25 (P1): правильное стерео вместо слепого Haas на ВСЁ.
        # Раньше Haas-задержка 12ms применялась ко всему треку, включая
        # кик и 808 — фазовые проблемы в низу, рыхлый саб в моно-сумме.
        # v25.1: моно-основа = всё ниже ~200 Гц (кик, 808, саб); Haas-задержка
        # применяется ТОЛЬКО к контенту выше 200 Гц (хэты, снейр-верх, атмосфера).
        # Иначе пологий кроссовер пропускает задержанный mid в низ и ломает
        # моно-совместимость (проверено smoke_v25.beat_lowband_mono).
        try:
            from scipy.signal import butter as _bt
            from scipy.signal import sosfilt as _sf_

            sos_hp200 = _bt(4, 200, btype="high", fs=sr, output="sos")
            mid_hi = _sf_(sos_hp200, y)  # контент >200 Гц (для ширины)
            low_mid = y - mid_hi  # моно-основа <200 Гц
            delay_samples = int(sr * 0.010)
            mid_hi_r = np.concatenate(
                [np.zeros(delay_samples, dtype="float32"), mid_hi[:-delay_samples]]
            )
            # верх (>5 кГц, хэты) ещё чуть шире — второй короткий Haas
            sos_hp5k = _bt(2, 5000, btype="high", fs=sr, output="sos")
            hi = _sf_(sos_hp5k, y)
            d2 = int(sr * 0.007)
            hi_r = np.concatenate([np.zeros(d2, dtype="float32"), hi[:-d2]])
            left = low_mid + mid_hi + hi * 0.25
            right = low_mid + mid_hi_r + hi_r * 0.35
            stereo = np.stack([left, right], axis=1)
        except Exception:
            try:
                delay_samples = int(sr * 0.012)
                left = y.copy()
                right = np.concatenate(
                    [np.zeros(delay_samples, dtype="float32"), y[:-delay_samples]]
                )
                stereo = np.stack([left, right], axis=1)
            except Exception:
                stereo = np.stack([y, y], axis=1)

        peak = float(np.max(np.abs(stereo)) + 1e-9)
        if peak > 0.98:
            stereo = stereo / peak * 0.95

        Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
        sf.write(out_wav, stereo, sr)
        return {
            "ok": True,
            "path": out_wav,
            "bpm": bpm,
            "key": key_name or f"{key_root} minor",
            "duration_sec": round(len(y) / sr, 2),
            "sections": section_info,
            "engine": "synth_beat_v22",
            "fallback_used": True,
            "reason": "synthesized structured beat (beat_constructor unavailable)",
        }
    except Exception as e:
        return {"ok": False, "reason": str(e)}

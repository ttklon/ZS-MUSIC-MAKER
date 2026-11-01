# -*- coding: utf-8 -*-
"""
app/core/stages/vocal.py — Вокал: TTS-синтез, конвертация голоса (RVC), вокальные эффекты.
"""

from __future__ import annotations

import logging

from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]


def _stage_voice_synth(lyrics_text: str, out_dir: Path) -> dict[str, Any]:
    out_wav = str(out_dir / "voice_preview.wav")
    if not lyrics_text or not lyrics_text.strip():
        return {
            "ok": False,
            "reason": "empty lyrics",
            "notice": "voice synth requires lyrics text",
        }
    fallback_attempts: list[dict[str, str]] = []

    def use_fallback() -> dict[str, Any]:
        result = dict(_pyttsx3_speak(lyrics_text, out_wav))
        if fallback_attempts:
            result["fallback_attempts"] = fallback_attempts
        return result

    try:
        from modules import voice_synth
    except Exception as exc:
        fallback_attempts.append({
            "engine": "voice_synth",
            "status": "unavailable",
            "error": f"{type(exc).__name__}: {exc}",
        })
        return use_fallback()

    if hasattr(voice_synth, "synth"):
        try:
            path = voice_synth.synth(
                lyrics_text, engine="auto", out_name=Path(out_wav).name
            )
            if path and Path(path).exists() and Path(path).stat().st_size > 1000:
                return {"ok": True, "path": path, "engine": "voice_synth.synth"}
            fallback_attempts.append({
                "engine": "voice_synth.synth",
                "status": "invalid_output",
                "error": "no usable audio path returned",
            })
        except Exception as exc:
            fallback_attempts.append({
                "engine": "voice_synth.synth",
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            })
    if hasattr(voice_synth, "synthesize"):
        try:
            result = voice_synth.synthesize(lyrics_text, out_wav)
            if isinstance(result, dict):
                return result
            if isinstance(result, str) and Path(result).exists():
                return {"ok": True, "path": result, "engine": "voice_synth"}
            fallback_attempts.append({
                "engine": "voice_synth.synthesize",
                "status": "invalid_output",
                "error": f"expected result dict or existing path, got {type(result).__name__}",
            })
        except Exception as exc:
            fallback_attempts.append({
                "engine": "voice_synth.synthesize",
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            })
    return use_fallback()


def _pyttsx3_speak(text: str, out_wav: str) -> dict[str, Any]:
    try:
        import pyttsx3

        eng = pyttsx3.init()
        eng.save_to_file(text, out_wav)
        eng.runAndWait()
        if Path(out_wav).exists() and Path(out_wav).stat().st_size > 1000:
            return {
                "ok": True,
                "path": out_wav,
                "engine": "pyttsx3",
                "fallback_used": True,
                "reason": "primary TTS unavailable; using pyttsx3",
            }
    except Exception:
        logging.getLogger(__name__).debug("ignored exception", exc_info=True)
    # v19: честный numpy-fallback — короткая "рыба" вокала с формантной
    # огибающей по слогам, чтобы пайплайн доехал до mix/master даже
    # без TTS. Помечается synthetic=True, blocked=True, engine='rap_scaffold'.
    # Скаффолд не выдаётся за вокал, не попадает в RVC (блокируется по blocked)
    # и в отчёте честно пишется, что реального вокала нет.
    try:
        import numpy as _np
        import soundfile as _sf

        sr = 22050
        # v22: структура по строкам и словам (было: только слова, сплошным потоком)
        lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
        if not lines:
            lines = ["текст пуст"]
        words_per_line = [ln.split() for ln in lines]
        # Формантные таблицы для русских гласных (Hz, примерные средние значения)
        formants = {
            "a": (730, 1090, 2440),
            "о": (500, 980, 2380),
            "у": (340, 880, 2240),
            "и": (280, 2250, 2890),
            "э": (550, 1770, 2490),
            "ы": (400, 1900, 2550),
            "е": (440, 1800, 2500),
            "я": (550, 1850, 2500),
            "ю": (300, 900, 2300),
            "ё": (400, 1700, 2400),
        }
        vowel_list = list(formants.keys())

        def _extract_vowel(word: str) -> str:
            wl = word.lower()
            for v in vowel_list:
                if v in wl:
                    return v
            return "a"

        # Собираем сегменты (слова) и паузы (между строками)
        segments = []  # list of (start_sample, end_sample, vowel, word_len)
        pause_sec_line = 0.32
        syll_sec = 0.24
        pause_sec_word = 0.05
        cur_sec = 0.0
        for line_i, words in enumerate(words_per_line):
            for word in words:
                vowel = _extract_vowel(word)
                n_syll_w = max(1, min(4, len(word) // 3))
                word_dur = n_syll_w * syll_sec
                segments.append((cur_sec, cur_sec + word_dur, vowel, len(word)))
                cur_sec += word_dur + pause_sec_word
            cur_sec += pause_sec_line
        total_dur = max(2.0, cur_sec)
        n = int(sr * total_dur)
        t = _np.arange(n) / sr
        y = _np.zeros(n, dtype="float32")

        for start_s, end_s, vowel, wlen in segments:
            s_idx = int(start_s * sr)
            e_idx = min(int(end_s * sr), n)
            if e_idx <= s_idx:
                continue
            tt = _np.arange(e_idx - s_idx) / sr
            # F0 с интонационным контуром: подъём на середине слова
            mid = (end_s - start_s) / 2
            f0_base = 110.0 + (wlen % 3) * 10.0
            f0 = f0_base + 12.0 * _np.sin(2 * _np.pi * 0.6 * tt) * _np.exp(
                -(((tt - mid) / (mid + 1e-6)) ** 2)
            )
            phase = 2 * _np.pi * _np.cumsum(f0) / sr
            # Источник: импульсная последовательность через синус+гармоники
            source = (
                0.55 * _np.sin(phase)
                + 0.22 * _np.sin(2 * phase)
                + 0.14 * _np.sin(3 * phase)
                + 0.05 * _np.sin(5 * phase)
            )
            # Формантная фильтрация (резонаторы F1/F2/F3 через простой pole-фильтр)
            f1, f2, f3 = formants.get(vowel, formants["a"])
            seg = source.copy()
            for f_c in (f1, f2, f3):
                # Простейший one-pole bandpass approximation
                try:
                    from scipy.signal import butter, sosfilt

                    fc_lo = max(50, f_c - 80)
                    fc_hi = min(sr / 2 - 100, f_c + 80)
                    if fc_hi > fc_lo:
                        sos = butter(
                            2, [fc_lo, fc_hi], btype="band", fs=sr, output="sos"
                        )
                        seg = seg + sosfilt(sos, seg) * 0.6
                except Exception:
                    # fallback: просто нормализуем
                    logging.getLogger(__name__).debug("ignored exception", exc_info=True)
            # Огибающая: attack + decay (форма слога)
            env = _np.exp(-tt * 3.5) * (1.0 - _np.exp(-tt * 60.0))
            seg = seg * env
            # Нормализуем сегмент
            peak_seg = _np.max(_np.abs(seg)) + 1e-9
            if peak_seg > 0:
                seg = seg / peak_seg * 0.75
            y[s_idx:e_idx] += seg.astype("float32")

        # Глобальная огибающая дыхания (медленная модуляция)
        breath_env = 1.0 + 0.08 * _np.sin(2 * _np.pi * 0.3 * t)
        y = y * breath_env.astype("float32")
        peak = float(_np.max(_np.abs(y)) + 1e-9)
        if peak > 0.9:
            y = y / peak * 0.9
        Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
        _sf.write(out_wav, y, sr)
        if Path(out_wav).exists() and Path(out_wav).stat().st_size > 1000:
            return {
                "ok": True,
                "path": out_wav,
                "engine": "rap_scaffold_numpy_v22",
                "synthetic": True,
                "blocked": True,
                "fallback_used": True,
                "reason": "no TTS engine (silero/xtts/bark/pyttsx3); "
                "numpy formant scaffold v22 (vowels, intonation, "
                "line pauses) used ONLY as pipeline placeholder "
                "— NOT a real voice, RVC will be blocked",
            }
    except Exception as e:
        return {
            "ok": False,
            "reason": f"no TTS + scaffold failed: {type(e).__name__}: {e}",
            "fallback_used": False,
            "notice": "voice synth requires pyttsx3/silero/xtts",
        }
    return {
        "ok": False,
        "reason": "no working TTS engine",
        "fallback_used": False,
        "notice": "voice synth requires pyttsx3/silero/xtts",
    }


def _stage_rvc(
    voice_wav: str, out_dir: Path, upstream_synthetic: bool = False
) -> dict[str, Any]:
    """v19: если upstream_synthetic (rap_scaffold), RVC обязан быть BLOCKED —
    кормить RVC чистую синтетику нельзя (станет ещё хуже).
    Правило P0.05: не выдавать pitch-shift/scaffold за RVC.
    """
    if upstream_synthetic:
        return {
            "ok": True,
            "blocked": True,
            "path": "",
            "reason": "upstream vocal is synthetic scaffold; "
            "RVC honestly BLOCKED (P0.05) — record real voice or install TTS",
        }
    try:
        from modules import rvc_manager

        out_wav = str(out_dir / "voice_rvc.wav")
        model_path = ROOT / "models" / "rvc" / "my_voice" / "my_voice.pth"
        if not model_path.exists():
            return {
                "ok": True,
                "blocked": True,
                "path": "",
                "reason": "no RVC .pth model at models/rvc/my_voice/my_voice.pth",
                "notice": "RVC BLOCKED — pitch-shift fallback refused (P0.05)",
            }
        r = rvc_manager.infer(
            voice_wav, voice_name="my_voice", out_name=out_wav
        )
        return {"ok": bool(r), "path": r or out_wav}
    except RuntimeError as e:
        return {"ok": True, "blocked": True, "path": "", "reason": str(e)}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def _stage_vocal_fx(vocal_wav: str | None, out_dir: Path) -> dict[str, Any]:
    """v18: vocal double + delay throw ДО микса (хитовая плотность хука).

    Применяется к вокалу после RVC (или к voice_draft, если RVC BLOCKED).
    Честный numpy-DSP (modules/vocal_fx.py). Если модуль недоступен или
    входа нет — ok=False / fallback, но НЕ ломает пайплайн: микс пойдёт
    на исходном вокале.
    """
    if not vocal_wav or not Path(vocal_wav).exists():
        return {"ok": False, "reason": "no vocal_wav upstream", "fallback_used": True}
    try:
        from modules import vocal_fx

        out_wav = str(out_dir / "voice_fx.wav")
        r = vocal_fx.process_vocal(vocal_wav, out_wav, use_double=True, use_throw=True)
        if isinstance(r, dict) and r.get("ok") and r.get("path"):
            return r
        # FX не критичен — возвращаем исходный вокал с честной пометкой
        return {
            "ok": True,
            "path": vocal_wav,
            "out_wav": vocal_wav,
            "engine": "bypass",
            "fallback_used": True,
            "reason": (r or {}).get("reason", "vocal_fx failed; bypass"),
        }
    except Exception as e:
        return {
            "ok": True,
            "path": vocal_wav,
            "out_wav": vocal_wav,
            "engine": "bypass",
            "fallback_used": True,
            "reason": f"vocal_fx import/run error: {e}",
        }

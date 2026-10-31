# -*- coding: utf-8 -*-
"""
app/core/ai/render.py — рендер-хелперы AI-пайплайна.

Чистые функции над загруженными моделями (handle): стерео-текстура MusicGen,
расширение бита интро/аутро, XTTS-вокал с фоллбеком, RVC-конвертация.
Состояния пайплайна здесь нет — всё приходит аргументами.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from app.ai.quality import validate_rvc_artifact, validate_vocal_artifact


def _slug(name: str) -> str:
    import re
    s = re.sub(r"[^A-Za-z0-9а-яА-ЯёЁ_-]+", "_", (name or "").strip()).strip("_")
    return s.lower() or "unknown"


def render_stereo_texture(handle, prompt: str, duration_sec: int, out_path: str) -> dict:
    """Рендерить отдельную стерео-текстуру через совместимый MusicGen handle."""
    try:
        import soundfile as sf

        handle.set_generation_params(
            duration=duration_sec, top_k=250, temperature=1.0, cfg_coef=3.0
        )
        generated = handle.generate([prompt], progress=False)[0].detach().cpu().numpy()
        if generated.ndim == 1:
            generated = generated[:, None]
        elif generated.ndim == 2:
            generated = generated.T
        else:
            return {"ok": False, "reason": "unexpected MusicGen stereo tensor shape"}
        if generated.shape[1] == 1:
            generated = generated.repeat(2, axis=1)
        sf.write(out_path, generated.astype("float32"), int(getattr(handle, "sample_rate", 32000)),
                 subtype="PCM_16")
        return {"ok": True, "texture_path": out_path}
    except Exception as exc:
        return {"ok": False, "reason": f"music_stereo generation failed: {exc}"}


def extend_beat_with_stereo_sections(
    base_path: str,
    intro_path: str,
    outro_path: str,
    out_path: str,
    fade_sec: float = 1.0,
) -> dict:
    """Stitch generated stereo intro/outro around a beat using equal-power fades."""
    try:
        import numpy as np
        import soundfile as sf

        def stereo(data):
            array = np.asarray(data, dtype="float32")
            if array.ndim == 1:
                return np.column_stack((array, array))
            if array.ndim != 2:
                raise ValueError("audio must be mono or stereo")
            if array.shape[1] == 1:
                return np.repeat(array, 2, axis=1)
            return array[:, :2]

        def resample(data, from_sr: int, to_sr: int):
            if from_sr == to_sr:
                return data
            from scipy.signal import resample_poly
            from math import gcd
            divisor = gcd(from_sr, to_sr)
            return resample_poly(data, to_sr // divisor, from_sr // divisor, axis=0).astype("float32")

        def crossfade(left, right, samples: int):
            overlap = min(samples, len(left), len(right))
            if overlap <= 0:
                return np.vstack((left, right))
            phase = np.linspace(0.0, np.pi / 2.0, overlap, endpoint=False, dtype="float32")
            mixed = left[-overlap:] * np.cos(phase)[:, None] + right[:overlap] * np.sin(phase)[:, None]
            return np.vstack((left[:-overlap], mixed, right[overlap:]))

        base, sample_rate = sf.read(base_path, always_2d=False)
        intro, intro_rate = sf.read(intro_path, always_2d=False)
        outro, outro_rate = sf.read(outro_path, always_2d=False)
        base = stereo(base)
        intro = resample(stereo(intro), int(intro_rate), int(sample_rate))
        outro = resample(stereo(outro), int(outro_rate), int(sample_rate))
        fade_samples = max(1, int(float(fade_sec) * sample_rate))
        stitched = crossfade(crossfade(intro, base, fade_samples), outro, fade_samples)
        peak = float(np.max(np.abs(stitched))) if len(stitched) else 0.0
        if peak > 0.98:
            stitched *= 0.98 / peak
        target = Path(out_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        sf.write(target, stitched, int(sample_rate), subtype="PCM_16")
        return {
            "ok": True,
            "beat_path": str(target),
            "sample_rate": int(sample_rate),
            "channels": 2,
            "duration_sec": len(stitched) / sample_rate,
            "fade_sec": float(fade_sec),
        }
    except Exception as exc:
        return {"ok": False, "reason": f"stereo beat extension failed: {exc}"}


def render_xtts_vocal(handle, text: str, out_path: str, speaker_wav: str | None = None) -> dict:
    """Синтезировать вокал через совместимый XTTS handle и подтвердить файл-результат."""
    try:
        kwargs = {"text": text, "file_path": out_path, "language": "ru"}
        if speaker_wav and Path(speaker_wav).exists():
            kwargs["speaker_wav"] = speaker_wav
        handle.tts_to_file(**kwargs)
        target = Path(out_path)
        if not target.exists() or target.stat().st_size <= 100:
            return {"ok": False, "reason": "XTTS did not produce an audio file"}
        quality = validate_vocal_artifact(target, text)
        return {
            "ok": bool(quality["ok"]),
            "vocal_path": str(target),
            "engine": "xtts_v2",
            "quality": quality,
            "reason": quality["reason"],
        }
    except Exception as exc:
        return {"ok": False, "reason": f"XTTS synthesis failed: {exc}"}


def render_voice_synth_fallback(text: str, out_path: str, synth_fn=None) -> dict:
    """Запустить существующую честную TTS-цепочку и привести результат к vocal-артефакту проекта."""
    try:
        if synth_fn is None:
            from modules.voice_synth import synth as synth_fn
        source_path = synth_fn(text, engine="auto", out_name=Path(out_path).name)
        source = Path(source_path) if source_path else None
        if source is None or not source.exists():
            return {"ok": False, "reason": "no fallback TTS engine produced audio"}
        target = Path(out_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        quality = validate_vocal_artifact(target, text)
        return {
            "ok": bool(quality["ok"]),
            "vocal_path": str(target),
            "engine": "voice_synth_fallback",
            "quality": quality,
            "reason": quality["reason"],
        }
    except Exception as exc:
        return {"ok": False, "reason": f"fallback TTS failed: {exc}"}


def render_rvc_vocal(handle, input_wav: str, out_path: str, voice_name: str, pitch_shift: int = 0) -> dict:
    """Выполнить RVC через публичный ``rvc_manager.infer`` и сохранить проектный артефакт."""
    try:
        safe_voice_name = Path(voice_name).name
        if not safe_voice_name:
            return {"ok": False, "reason": "RVC voice name is missing"}
        produced = handle.infer(
            input_wav=input_wav,
            voice_name=safe_voice_name,
            pitch_shift=int(pitch_shift),
            out_name=Path(out_path).name,
        )
        source = Path(produced) if produced else None
        if source is None or not source.exists() or source.stat().st_size <= 100:
            return {"ok": False, "reason": "RVC did not produce an audio file"}
        target = Path(out_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        quality = validate_rvc_artifact(input_wav, target)
        return {
            "ok": bool(quality["ok"]),
            "vocal_path": str(target),
            "engine": "rvc",
            "voice_name": safe_voice_name,
            "pitch_shift": int(pitch_shift),
            "quality": quality,
            "reason": quality["reason"],
        }
    except Exception as exc:
        return {"ok": False, "reason": f"RVC inference failed: {exc}"}

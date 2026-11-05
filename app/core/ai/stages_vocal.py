# -*- coding: utf-8 -*-
"""
app/core/ai/stages_vocal.py — вокал и микс AI-пайплайна.

XTTS → честный voice_synth-фоллбек, RVC-конвертация, микс бита с вокалом и
атмосферной текстурой.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.core.ai.context import AIContext
from app.core.ai.render import render_rvc_vocal, render_voice_synth_fallback


def stage_vocal(handle, ctx):
    ai: AIContext = ctx["ai"]
    if ai.dry_run:
        return {"skipped": "dry-run"}
    lyrics = (ctx["sink"].get("lyrics") or {}).get("lyrics") or ""
    if not lyrics.strip():
        return {"skipped": "no lyrics"}
    import re
    clean = re.sub(r"^\[.*?\]\s*$", "", lyrics, flags=re.MULTILINE).strip()
    clean = re.sub(r"\n{3,}", "\n\n", clean)[:3500]
    out_path = str(ai.out_root / "vocal_xtts.wav")
    speaker_wav = ai.ws.get("speaker_wav")
    if not speaker_wav:
        try:
            from modules.voice_vault import select_speaker_wav
            speaker_wav = select_speaker_wav(ai.ws.get("vocal_style"))
        except Exception:
            speaker_wav = None
    if handle is not None:
        from modules.voice_synth_ai import synth_vocal_ai

        primary = synth_vocal_ai(
            clean,
            out_path,
            speaker_wav=speaker_wav,
            language="ru",
            tts_handle=handle,
        )
        if primary.get("ok"):
            return primary
    else:
        primary = {"ok": False, "reason": "XTTS model unavailable"}
    fallback = render_voice_synth_fallback(clean, out_path)
    fallback["xtts_attempt"] = primary.get("reason")
    return fallback

def stage_rvc(handle, ctx):
    ai: AIContext = ctx["ai"]
    if ai.dry_run:
        return {"skipped": "dry-run"}
    if handle is None:
        return {"skipped": "RVC unavailable", "reason": "no installed RVC model/runtime"}
    vocal = (ctx["sink"].get("vocal_synth") or {}).get("vocal_path")
    if not vocal or not Path(vocal).exists():
        return {"skipped": "no vocal"}
    voice_name = ai.ws.get("rvc_voice_name") or Path(str(ai.ws.get("rvc_model") or "")).stem
    if not voice_name:
        return {"skipped": "no rvc_voice_name"}
    out_path = str(ai.out_root / "vocal_rvc.wav")
    return render_rvc_vocal(
        handle,
        vocal,
        out_path,
        voice_name=voice_name,
        pitch_shift=int(ai.ws.get("rvc_pitch_shift", 0)),
    )

def stage_mix(_, ctx):
    ai: AIContext = ctx["ai"]
    beat = ((ctx["sink"].get("music_stereo") or {}).get("beat_path")
            or (ctx["sink"].get("music") or {}).get("beat_path"))
    vocal = ((ctx["sink"].get("rvc") or {}).get("vocal_path")
             or (ctx["sink"].get("vocal_synth") or {}).get("vocal_path"))
    texture = (ctx["sink"].get("music_stereo") or {}).get("texture_path")
    mix_path = str(ai.out_root / "mix.wav")
    if not beat or not Path(beat).exists():
        return {"skipped": "no beat"}
    try:
        import numpy as np, soundfile as sf
        b, sr_b = sf.read(beat)
        if b.ndim == 1:
            b = np.stack([b, b], axis=-1)
        texture_mixed = False
        if texture and Path(texture).exists():
            t, sr_t = sf.read(texture)
            if sr_t != sr_b:
                import librosa
                t = librosa.resample(t.T if t.ndim > 1 else t, orig_sr=sr_t, target_sr=sr_b)
                t = t.T if t.ndim > 1 else t
            if t.ndim == 1:
                t = np.stack([t, t], axis=-1)
            n_texture = min(len(b), len(t))
            beat_rms = float(np.sqrt(np.mean(b[:n_texture] ** 2)) + 1e-9)
            texture_rms = float(np.sqrt(np.mean(t[:n_texture] ** 2)) + 1e-9)
            texture_gain = (beat_rms * (10.0 ** (-18.0 / 20.0))) / texture_rms
            b[:n_texture] = b[:n_texture] + t[:n_texture] * min(texture_gain, 1.0)
            texture_mixed = True
        if not vocal or not Path(vocal).exists():
            peak = float(np.max(np.abs(b)) + 1e-9)
            if peak > 0.99:
                b = b * (0.98 / peak)
            sf.write(mix_path, b, sr_b)
            return {"ok": True, "mix_path": mix_path, "vocal": False, "texture_mixed": texture_mixed}
        v, sr_v = sf.read(vocal)
        if sr_v != sr_b:
            import librosa
            v = librosa.resample(v.T if v.ndim > 1 else v, orig_sr=sr_v, target_sr=sr_b)
            v = v.T if v.ndim > 1 else v
        if v.ndim == 1:
            v = np.stack([v, v], axis=-1)
        n = min(len(b), len(v))
        mix = b[:n] * 0.9 + v[:n] * 0.75
        peak = float(np.max(np.abs(mix)) + 1e-9)
        if peak > 0.99:
            mix = mix * (0.98 / peak)
        sf.write(mix_path, mix, sr_b)
        return {"ok": True, "mix_path": mix_path, "vocal": True, "texture_mixed": texture_mixed}
    except Exception as e:
        return {"ok": False, "reason": str(e)}

# -*- coding: utf-8 -*-
"""
app/core/ai/stages_music.py — генерация бита AI-пайплайна.

Основной бит (нейродвижок или честный CyberSynth-фоллбек) и расширение
стерео-текстурой MusicGen с валидацией артефакта.
"""

from __future__ import annotations

from pathlib import Path

from app.core.ai.context import AIContext
from app.core.ai.render import extend_beat_with_stereo_sections, render_stereo_texture
from app.ai import prompts as P
from app.ai.quality import validate_audio_artifact, validate_stereo_texture


def stage_music(handle, ctx):
    ai: AIContext = ctx["ai"]
    if ai.dry_run:
        return {"ok": True, "beat_path": "[dry]"}
    out_path = str(ai.out_root / "beat.wav")
    if handle is None:
        try:
            from modules.cyber_synth import CyberSynth

            result = CyberSynth().synthesize_track(
                bpm=ai.ws["bpm"], duration_sec=ai.ws["duration_sec"], out_path=out_path
            )
            result = dict(result) if isinstance(result, dict) else {}
            result["engine"] = "cyber_synth_fallback"
            result["beat_path"] = out_path
        except Exception as exc:
            return {"ok": False, "reason": f"no music engine: {exc}"}
    else:
        art = (ctx["sink"].get("dossier_load") or {}).get("artist_dossier")
        track = (ctx["sink"].get("dossier_load") or {}).get("track_dossier")
        instruments = track.get("reusable_elements", [])[:5] if isinstance(track, dict) else []
        reference_features = {
            "instruments": instruments,
            "atmosphere": (art or {}).get("flow", ""),
        } if art else None
        prompt = P.build_music_prompt(
            ai.ws["genre"], ai.ws["bpm"], ai.ws["key"], ai.ws["mood"],
            reference_artist=ai.ws.get("reference_artist") or ai.ws.get("ai.artist_slug"),
            reference_track_features=reference_features,
        )
        from modules.beat_gen_ai import render_beat_ai

        result = render_beat_ai(
            prompt=prompt,
            bpm=ai.ws["bpm"],
            duration_sec=ai.ws["duration_sec"],
            out_path=out_path,
            reference_wav=ai.ws.get("reference_wav"),
            handle=handle,
        )
        result["prompt"] = prompt
    quality = validate_audio_artifact(
        out_path, min_duration_sec=max(1.0, min(5.0, ai.ws["duration_sec"] * 0.5))
    )
    result["quality"] = quality
    result["reason"] = quality["reason"]
    result["ok"] = bool(result.get("ok", True)) and bool(quality["ok"])
    return result

def _stereo_textures(handle, prompt: str, ai: AIContext, duration: int):
    """Отрисовать интро и аутро. Возвращает (intro, outro) или отказ."""
    intro_path = str(ai.out_root / "texture_intro_stereo.wav")
    outro_path = str(ai.out_root / "texture_outro_stereo.wav")
    intro = render_stereo_texture(
        handle, prompt + ", wide stereo intro, gentle fade-in, no lead vocal", duration, intro_path
    )
    outro = render_stereo_texture(
        handle, prompt + ", wide stereo outro, resolving fade-out, no lead vocal", duration, outro_path
    )
    return intro, outro


def _texture_rejection(sections, duration: int):
    """Первая сломанная или не прошедшая качество текстура — как отказ стадии."""
    for section in sections:
        # ВАЖНО: переменную нельзя называть `handle` — она перекрывает аргумент
        # модели, и следующий вызов render_stereo_texture получает строку-путь
        # вместо загруженной модели ("'str' object has no attribute ...").
        texture_path = section.get("texture_path")
        if not section.get("ok") or not texture_path:
            return (
                "music_stereo generation failed",
                section.get("reason", "texture did not render"),
            )
        quality = validate_stereo_texture(
            texture_path, min_duration_sec=max(1.0, duration * 0.5)
        )
        if not quality["ok"]:
            return "music_stereo quality rejected", quality["reason"]
    return None


def stage_music_stereo(handle, ctx):
    ai: AIContext = ctx["ai"]
    """Extend the base beat with MusicGen stereo intro/outro through crossfades."""
    if ai.dry_run:
        return {"skipped": "dry-run", "fallback": "base beat is preserved"}
    base_beat = (ctx["sink"].get("music") or {}).get("beat_path")
    if not base_beat or not Path(base_beat).exists():
        return {"skipped": "no base beat", "fallback": "base beat is unavailable"}
    if handle is None:
        return {
            "skipped": "music_stereo unavailable",
            "reason": "audiocraft model is not installed or not loadable",
            "fallback": "base beat is preserved without a synthetic extension",
        }
    prompt = P.build_music_prompt(ai.ws["genre"], ai.ws["bpm"], ai.ws["key"], ai.ws["mood"])
    duration = max(2, min(int(ai.ws.get("texture_duration_sec", 8)), 20))
    intro, outro = _stereo_textures(handle, prompt, ai, duration)
    rejection = _texture_rejection((intro, outro), duration)
    if rejection:
        return {
            "skipped": rejection[0],
            "reason": rejection[1],
            "fallback": "base beat is preserved without a synthetic extension",
        }
    result = extend_beat_with_stereo_sections(
        str(base_beat),
        str(intro["texture_path"]),
        str(outro["texture_path"]),
        str(ai.out_root / "beat_stereo_extended.wav"),
        fade_sec=float(ai.ws.get("texture_crossfade_sec", 1.0)),
    )
    if not result.get("ok"):
        result.update({"skipped": "stereo extension failed", "fallback": "base beat is preserved"})
        return result
    quality = validate_audio_artifact(result["beat_path"], min_duration_sec=1.0)
    result.update({
        "ok": bool(quality["ok"]),
        "quality": quality,
        "reason": quality["reason"],
        "engine": "musicgen-stereo-medium",
        "intro_path": intro["texture_path"],
        "outro_path": outro["texture_path"],
        "extension_sec": duration * 2,
    })
    return result

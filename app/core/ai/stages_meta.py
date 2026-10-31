# -*- coding: utf-8 -*-
"""
app/core/ai/stages_meta.py — метаданные AI-пайплайна.

Проверка железа, загрузка досье артиста/трека, генерация и валидация текста,
метаданные для площадок. Недоступность модели — честный fallback/skip.
"""

from __future__ import annotations

import json

from app.core.ai.context import AIContext
from app.core.logger import app_logger
from app.ai import prompts as P
from app.ai import llm_service as LLM
from app.ai.quality import validate_metadata_json, validate_song_lyrics
from modules.artist_dossier import DossierManager


def stage_hw(_, ctx):
    try:
        from app.core.hw_autodetect import get_hardware_profile
        return get_hardware_profile()
    except Exception as e:
        return {"error": str(e)}

def stage_dossier_load(_, ctx):
    ai: AIContext = ctx["ai"]
    if not ai.artist_slug:
        return {"skipped": "no artist_slug"}
    mgr = DossierManager()
    return {"artist_dossier": mgr.get_artist_dossier(ai.artist_slug),
            "track_dossier": mgr.get_track_dossier(ai.artist_slug, ai.ref_track_id) if ai.ref_track_id else None}

def stage_lyrics(handle, ctx):
    ai: AIContext = ctx["ai"]
    if ai.dry_run:
        return {"ok": True, "lyrics": "[dry-run]", "source": "dry"}
    requested_lines = ai.ws.get("user_lyrics_lines") or []
    text, source = "", "lyrics_llm"
    quality = {"ok": False, "reason": "lyrics_llm unavailable", "metrics": {}}
    if handle is not None:
        try:
            from modules.lyrics_gen import generate_lyrics_ai

            ai_result = generate_lyrics_ai(
                theme=ai.ws["theme"],
                style_vector={"target_bpm": ai.ws["bpm"]},
                n_verses=ai.ws["n_verses"],
                user_lyrics_lines=requested_lines,
                bilingual=ai.ws["bilingual"],
                artist_slug=ai.artist_slug,
                track_id=ai.ref_track_id,
                genre=ai.ws["genre"],
                handle=handle,
            )
            text = str(ai_result.get("lyrics") or "")
            source = str(ai_result.get("source") or "lyrics_llm")
            quality = validate_song_lyrics(text, user_lines=requested_lines)
        except Exception as exc:  # noqa: BLE001
            app_logger.error("[orchestrator_ai] stage=lyrics event=ai_failed reason=%s", exc)
            quality = {"ok": False, "reason": f"lyrics_ai failed: {exc}", "metrics": {}}
    if not quality["ok"]:
        try:
            from modules import lyrics_gen

            fallback = lyrics_gen.generate_lyrics(
                theme=ai.ws["theme"],
                style_vector={"target_bpm": ai.ws["bpm"]},
                n_verses=ai.ws["n_verses"],
                user_lyrics_lines=requested_lines,
                bilingual=ai.ws["bilingual"],
            )
            text = str(fallback.get("lyrics") or "")
            source = "punch_lib_fallback"
            quality = validate_song_lyrics(text, user_lines=requested_lines)
        except Exception as exc:  # noqa: BLE001
            app_logger.error("[orchestrator_ai] stage=lyrics event=fallback_failed reason=%s", exc)
    (ai.out_root / "lyrics.txt").write_text(text or "", encoding="utf-8")
    return {"ok": bool(quality["ok"]), "lyrics": text, "source": source,
            "path": str(ai.out_root / "lyrics.txt"), "quality": quality,
            "reason": quality["reason"]}

def _metadata_fallback(ai: AIContext) -> dict[str, object]:
    """Create genre-aware metadata that satisfies the release quality contract."""
    genre = str(ai.ws.get("genre") or "music").strip() or "music"
    theme = " ".join(str(ai.ws.get("theme") or "").split()).strip()
    mood = " ".join(str(ai.ws.get("mood") or "").split()).strip() or "выразительное"
    title = theme[:80] or f"{genre.title()} Pulse"
    if len(title) < 3:
        title = f"{genre.title()} Pulse"
    return {
        "title": title,
        "spotify_desc": (
            f"Независимый {genre}-релиз «{title}» с настроением {mood}. "
            "Трек создан для внимательного прослушивания и ночной дороги."
        )[:400],
        "youtube_desc": (
            f"«{title}» — новый {genre}-трек о теме «{theme or title}» и настроении {mood}. "
            "Слушайте релиз, сохраняйте и делитесь с теми, кому близен этот звук."
        )[:400],
        "tags_tiktok": [genre, "newmusic", "independent"],
        "tags_instagram": ["music", "release", "underground"],
    }

def stage_metadata(handle, ctx):
    ai: AIContext = ctx["ai"]
    lyrics = (ctx["sink"].get("lyrics") or {}).get("lyrics") or ""
    fallback = _metadata_fallback(ai)
    source = "metadata_fallback"
    if ai.dry_run:
        js, source = fallback, "dry"
    elif handle is not None:
        js = LLM.complete_json(handle, P.SYSTEM_METADATA,
            P.build_metadata_prompt(ai.ws["theme"], ai.ws["genre"], lyrics),
            max_tokens=1200, temperature=0.6) or {}
        source = "metadata_llm"
    else:
        js = fallback
    quality = validate_metadata_json(js)
    if not quality["ok"]:
        js, source = fallback, "metadata_fallback"
        quality = validate_metadata_json(js)
    js = dict(js)
    js.update({"ok": bool(quality["ok"]), "source": source, "quality": quality,
               "reason": quality["reason"]})
    (ai.out_root / "metadata.json").write_text(
        json.dumps(js, ensure_ascii=False, indent=2), encoding="utf-8")
    return js

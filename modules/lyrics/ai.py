# -*- coding: utf-8 -*-
"""
modules/lyrics/ai.py — AI-first генерация через локальную роль `lyrics_llm`.

Возвращает тот же контракт, что и базовый генератор. Если весов/рантайма нет,
честно отвечает `ok=False, source="BLOCKED"`, а не подсовывает шаблон.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any, Dict

from modules.lyrics.memory import LYRIC_MEMORY as MEMORY
from modules.lyrics.memory import VAULT_DIR as VAULT


def generate_lyrics_ai(theme, style_vector=None, n_verses=2, user_lyrics_lines=None,
                       bilingual=True, artist_slug=None, track_id=None,
                       genre="phonk", handle: Any = None) -> Dict[str, Any]:
    from app.ai import llm_service as LLM
    from app.ai import prompts as P
    from app.ai.registry import registry
    from modules.artist_dossier import DossierManager

    style_vector = style_vector or {}
    user_lyrics_lines = [l.strip() for l in (user_lyrics_lines or []) if l.strip()]
    bpm = int(style_vector.get("target_bpm") or 140)
    art_dos = trk_dos = None
    if artist_slug:
        mgr = DossierManager()
        art_dos = mgr.get_artist_dossier(artist_slug)
        trk_dos = mgr.get_track_dossier(artist_slug, track_id) if track_id else None
    prompt = P.build_lyrics_prompt(theme=theme, genre=genre, bpm=bpm,
                                   n_verses=n_verses, bilingual=bilingual,
                                   user_lines=user_lyrics_lines,
                                   artist_dossier=art_dos, track_reference=trk_dos)
    if handle is None and not registry.is_available("lyrics_llm"):
        return {"ok": False, "lyrics": "",
                "reason": "lyrics_llm unavailable - run tools/pull_ai_models.py --role lyrics_llm",
                "source": "BLOCKED"}
    if handle is None:
        with registry.use("lyrics_llm") as loaded:
            text = LLM.complete(loaded.handle, P.SYSTEM_LYRICS, prompt,
                                max_tokens=1400, temperature=0.9, top_p=0.95,
                                repeat_penalty=1.15)
    else:
        text = LLM.complete(handle, P.SYSTEM_LYRICS, prompt,
                            max_tokens=1400, temperature=0.9, top_p=0.95,
                            repeat_penalty=1.15)
    if not text or len(text) < 60:
        return {"ok": False, "lyrics": text or "", "reason": "empty LLM output",
                "source": "lyrics_llm"}
    text = re.sub(r"^```.*?$", "", text, flags=re.MULTILINE).strip()
    lo = text.lower()
    missing = [ln for ln in user_lyrics_lines if ln.lower() not in lo]
    if missing:
        text = text.rstrip() + "\n\n[User]\n" + "\n".join(missing)
    VAULT.mkdir(parents=True, exist_ok=True)
    with open(MEMORY, "a", encoding="utf-8") as f:
        f.write(json.dumps({"theme": theme, "bpm": bpm, "lyrics": text,
                            "source": "lyrics_llm", "artist_slug": artist_slug,
                            "track_id": track_id, "timestamp": time.time()},
                           ensure_ascii=False) + "\n")
    return {"ok": True, "lyrics": text, "source": "lyrics_llm",
            "bilingual": bilingual, "n_verses": n_verses, "bpm": bpm,
            "artist_slug": artist_slug, "track_id": track_id,
            "user_lines_included": all(l.lower() in text.lower() for l in user_lyrics_lines)}

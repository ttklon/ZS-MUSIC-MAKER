# -*- coding: utf-8 -*-
"""ZS Music Maker - modules/cover_art_ai.py (v38, SDXL Base 1.0 fp16)."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict
from app.ai.registry import registry
from app.ai import prompts as P

ROOT = Path(__file__).resolve().parents[1]
PRESETS_DIR = ROOT / "data" / "genre_presets"


def cover_direction_for_genre(genre: str, mood: str, key: str = "unknown") -> str:
    """Render the versioned prompt_cover template for a known genre, otherwise use a safe generic direction."""
    safe_name = Path(str(genre)).name
    path = PRESETS_DIR / f"{safe_name}.json"
    fallback = (
        "Square album cover for {genre}: {mood} mood, {key} tonal palette, "
        "visual motifs of rhythmic drums, bass and atmospheric light; original editorial artwork."
    )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        template = str(payload.get("prompt_cover") or fallback)
        instruments = str(payload.get("cover_instruments") or "rhythmic drums, bass and atmospheric light")
    except (OSError, json.JSONDecodeError):
        template = fallback
        instruments = "rhythmic drums, bass and atmospheric light"
    try:
        return template.format(genre=genre, mood=mood, key=key, instruments=instruments)
    except (KeyError, ValueError):
        return fallback.format(genre=genre, mood=mood, key=key, instruments=instruments)


def render_cover_with_pipeline(pipe: Any, prompt: str, out_path: str, size: int = 1024) -> Dict[str, Any]:
    """Отрендерить cover через уже загруженный SDXL pipeline из SequentialAIRunner."""
    try:
        image = pipe(
            prompt=prompt,
            num_inference_steps=30,
            guidance_scale=7.0,
            width=size,
            height=size,
        ).images[0]
        image.save(out_path)
        return {"ok": True, "engine": "sdxl-base-1.0", "path": out_path, "prompt": prompt}
    except Exception as exc:
        return {"ok": False, "reason": f"SDXL cover generation failed: {exc}", "engine": "sdxl-base-1.0"}


def render_cover_ai(title: str, artist: str, genre: str, mood: str,
                    out_path: str, size: int = 1024, handle: Any = None,
                    key: str = "unknown") -> Dict[str, Any]:
    direction = cover_direction_for_genre(genre, mood, key=key)
    prompt = P.build_cover_prompt(title, artist, genre, mood, genre_direction=direction)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    if handle is not None:
        return render_cover_with_pipeline(handle, prompt, out_path, size=size)
    if not registry.is_available("cover_art"):
        try:
            from modules import cover_art_gen
            res = cover_art_gen.generate(title=title, artist=artist,
                                         out_path=out_path, style="gradient", size=size)
            res["engine"] = "PIL_fallback"
            res["prompt"] = prompt
            return res
        except Exception as e:
            return {"ok": False, "reason": f"no cover engine: {e}"}
    with registry.use("cover_art") as m:
        return render_cover_with_pipeline(m.handle, prompt, out_path, size=size)

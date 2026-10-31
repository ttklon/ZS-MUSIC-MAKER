# -*- coding: utf-8 -*-
"""
app/core/ai/stages_final.py — финал AI-пайплайна.

Мастеринг (matchering по референсу либо DSP-чейн), обложка и авто-теги по
аудио. Каждая стадия валидирует артефакт и возвращает честный ok/reason.
"""

from __future__ import annotations

from pathlib import Path

from app.core.ai.context import AIContext
from app.ai.quality import validate_cover_artifact, validate_master_artifact


def stage_master(handle, ctx):
    ai: AIContext = ctx["ai"]
    mix = (ctx["sink"].get("mix") or {}).get("mix_path")
    if not mix:
        return {"skipped": "no mix"}
    out_master = str(ai.out_root / "masters" / "master_ai.wav")
    from modules.mastering_reference import master_ai
    result = master_ai(
        mix,
        out_master,
        reference_wav=ai.ws.get("reference_master_wav"),
        target_lufs=-14.0,
        handle=handle,
    )
    if result.get("ok") and result.get("path"):
        quality = validate_master_artifact(
            mix, result["path"], max_true_peak_dbtp=-1.0
        )
        result["quality"] = quality
        result["ok"] = bool(quality["ok"])
        result["reason"] = quality["reason"]
    return result

def stage_cover(handle, ctx):
    ai: AIContext = ctx["ai"]
    meta = ctx["sink"].get("metadata") or {}
    title = meta.get("title") or ai.ws.get("theme", "Untitled")
    artist = ai.ws.get("artist_display") or ai.ws.get("ai.artist_slug") or "ZS"
    from modules.cover_art_ai import render_cover_ai
    result = render_cover_ai(
        title=title,
        artist=artist,
        genre=ai.ws["genre"],
        mood=ai.ws["mood"],
        out_path=str(ai.out_root / "cover.png"),
        handle=handle,
        key=ai.ws["key"],
    )
    if result.get("ok") and result.get("path"):
        quality = validate_cover_artifact(
            result["path"], min_size=1024, min_bytes=100_000
        )
        result["ok"] = bool(quality["ok"])
        result["quality"] = quality
        result["reason"] = quality["reason"]
    return result

def stage_tag(bundle, ctx):
    ai: AIContext = ctx["ai"]
    if bundle is None:
        return {"skipped": "no clap"}
    master = ((ctx["sink"].get("master") or {}).get("path")
              or str(ai.out_root / "masters" / "master_ai.wav"))
    if not Path(master).exists():
        return {"skipped": "no master"}
    try:
        import torch, librosa, numpy as np
        model, proc = bundle
        y, sr = librosa.load(master, sr=48000, mono=True, duration=30)
        cand = ["phonk", "trap", "drill", "pop", "rock", "shanson",
                "aggressive", "melancholic", "party", "romantic"]
        inputs = proc(text=cand, audios=y, sampling_rate=48000,
                      return_tensors="pt", padding=True)
        if any(p.is_cuda for p in model.parameters()):
            inputs = {k: (v.cuda() if hasattr(v, "cuda") else v)
                      for k, v in inputs.items()}
        with torch.no_grad():
            logits = model(**inputs).logits_per_audio[0].cpu().numpy()
        tags = [cand[i] for i in np.argsort(-logits)[:5]]
        return {"ok": True, "tags": tags, "goal": ai.ws["genre"],
                "match_genre": ai.ws["genre"] in tags}
    except Exception as e:
        return {"ok": False, "reason": str(e)}

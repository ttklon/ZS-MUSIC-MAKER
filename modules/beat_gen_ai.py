# -*- coding: utf-8 -*-
"""ZS Music Maker - modules/beat_gen_ai.py (v38, MusicGen-large, чанки 20с)."""
from __future__ import annotations
import math
from pathlib import Path
from typing import Any, Dict, Optional
from app.ai.registry import registry


def render_beat_ai(prompt: str, bpm: int = 140, duration_sec: int = 120,
                   out_path: str = "beat.wav", reference_wav: Optional[str] = None,
                   chunk_sec: int = 20) -> Dict[str, Any]:
    if not registry.is_available("music_generation"):
        return {"ok": False, "reason": "music_generation unavailable - install audiocraft"}
    import numpy as np, soundfile as sf, torch
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    n_chunks = max(1, math.ceil(duration_sec / chunk_sec))
    with registry.use("music_generation") as m:
        model = m.handle
        try:
            model.set_generation_params(duration=min(chunk_sec, 30), top_k=250,
                                        top_p=0.0, temperature=1.0, cfg_coef=3.0)
        except Exception:
            pass
        sr = getattr(model, "sample_rate", 32000)
        chunks = [model.generate([prompt], progress=False)[0].cpu().numpy()]
        for i in range(1, n_chunks):
            try:
                prev_t = torch.from_numpy(chunks[-1]).unsqueeze(0)
                if any(p.is_cuda for p in model.lm.parameters()):
                    prev_t = prev_t.cuda()
                cont = model.generate_continuation(prev_t, sr, [prompt], progress=False)[0]
                chunks.append(cont.cpu().numpy())
            except Exception:
                chunks.append(model.generate([prompt], progress=False)[0].cpu().numpy())
    full = np.concatenate(chunks, axis=-1)
    total = int(duration_sec * sr)
    if full.shape[-1] > total:
        full = full[..., :total]
    if full.ndim == 1:
        full = np.stack([full, full], axis=-1)
    else:
        full = full.T
        if full.shape[1] == 1:
            full = np.concatenate([full, full], axis=1)
    peak = float(np.max(np.abs(full)) + 1e-9)
    if peak > 0.99:
        full = full * (0.98 / peak)
    sf.write(out_path, full.astype("float32"), int(sr), subtype="PCM_16")
    return {"ok": True, "beat_path": out_path, "duration_sec": duration_sec,
            "sample_rate": int(sr), "bpm": bpm, "engine": "musicgen-large",
            "chunks": n_chunks}

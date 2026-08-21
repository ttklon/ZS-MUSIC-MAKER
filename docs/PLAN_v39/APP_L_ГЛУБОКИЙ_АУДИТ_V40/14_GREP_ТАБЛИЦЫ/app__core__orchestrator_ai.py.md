# grep-таблицы `app/core/orchestrator_ai.py`

## `import` — 23 совпадений
```
    3 | from __future__ import annotations
    4 | import json, math, shutil
    5 | from pathlib import Path
    6 | from app.core.logger import app_logger
    7 | from app.ai.sequential_runner import SequentialAIRunner, AIStage
    8 | from app.ai import prompts as P
    9 | from app.ai import llm_service as LLM
   10 | from app.ai.quality import (
   18 | from modules.artist_dossier import DossierManager
   22 |     import re
   30 |         import soundfile as sf
   77 |             from modules.voice_synth import synth as synth_fn
  134 |         from config.settings import get_settings
  157 |             from app.core.hw_autodetect import get_hardware_profile
  186 |                 from modules import lyrics_gen
  238 |                 from modules.cyber_synth import CyberSynth
  260 |         import numpy as np, soundfile as sf, torch
  333 |         import re
  375 |             import numpy as np, soundfile as sf
  384 |                 import librosa
  404 |         from modules.mastering_ai import master_ai
  412 |         from modules.cover_art_ai import render_cover_ai
  424 |             import torch, librosa, numpy as np
```

## `except` — 12 совпадений
```
   47 |     except Exception as exc:
   69 |     except Exception as exc:
   94 |     except Exception as exc:
  127 |     except Exception as exc:
  137 |     except Exception:  # noqa: BLE001
  159 |         except Exception as e:
  194 |             except Exception as _lg_e:  # noqa: BLE001
  250 |             except Exception as e:
  265 |         except Exception:
  277 |             except Exception:
  396 |         except Exception as e:
  439 |         except Exception as e:
```

## `try` — 12 совпадений
```
   29 |     try:
   53 |     try:
   75 |     try:
  100 |     try:
  133 |     try:
  156 |         try:
  185 |             try:
  237 |             try:
  263 |         try:
  271 |             try:
  374 |         try:
  423 |         try:
```

## `def` — 18 совпадений
```
   21 | def _slug(name: str) -> str:
   27 | def render_stereo_texture(handle, prompt: str, duration_sec: int, out_path: str) -> dict:
   51 | def render_xtts_vocal(handle, text: str, out_path: str, speaker_wav: str | None = None) -> dict:
   73 | def render_voice_synth_fallback(text: str, out_path: str, synth_fn=None) -> dict:
   98 | def render_rvc_vocal(handle, input_wav: str, out_path: str, voice_name: str, pitch_shift: int = 0) -> dict:
  131 | def run_ai_pipeline(project_id, wizard_state=None, out_root=None, dry_run=False):
  155 |     def stage_hw(_, ctx):
  162 |     def stage_dossier_load(_, ctx):
  169 |     def stage_lyrics(handle, ctx):
  203 |     def stage_metadata(handle, ctx):
  233 |     def stage_music(handle, ctx):
  300 |     def stage_music_stereo(handle, ctx):
  327 |     def stage_vocal(handle, ctx):
  347 |     def stage_rvc(handle, ctx):
  367 |     def stage_mix(_, ctx):
  399 |     def stage_master(_, ctx):
  408 |     def stage_cover(_, ctx):
  416 |     def stage_tag(bundle, ctx):
```

## `return` — 49 совпадений
```
   24 |     return s.lower() or "unknown"
   41 |             return {"ok": False, "reason": "unexpected MusicGen stereo tensor shape"}
   46 |         return {"ok": True, "texture_path": out_path}
   48 |         return {"ok": False, "reason": f"music_stereo generation failed: {exc}"}
   60 |             return {"ok": False, "reason": "XTTS did not produce an audio file"}
   62 |         return {
   70 |         return {"ok": False, "reason": f"XTTS synthesis failed: {exc}"}
   81 |             return {"ok": False, "reason": "no fallback TTS engine produced audio"}
   87 |         return {
   95 |         return {"ok": False, "reason": f"fallback TTS failed: {exc}"}
  103 |             return {"ok": False, "reason": "RVC voice name is missing"}
  112 |             return {"ok": False, "reason": "RVC did not produce an audio file"}
  118 |         return {
  128 |         return {"ok": False, "reason": f"RVC inference failed: {exc}"}
  158 |             return get_hardware_profile()
  160 |             return {"error": str(e)}
  164 |             return {"skipped": "no artist_slug"}
  166 |         return {"artist_dossier": mgr.get_artist_dossier(artist_slug),
  171 |             return {"ok": True, "lyrics": "[dry-run]", "source": "dry"}
  199 |         return {"ok": bool(quality["ok"]), "lyrics": text, "source": source,
  231 |         return js
  235 |             return {"ok": True, "beat_path": "[dry]"}
  249 |                 return res
  251 |                 return {"ok": False, "reason": f"no music engine: {e}"}
  296 |         return {"ok": bool(quality["ok"]), "beat_path": out_path, "engine": "musicgen-large",
  303 |             return {"skipped": "dry-run"}
  305 |             return {
  325 |         return result
  329 |             return {"skipped": "dry-run"}
  332 |             return {"skipped": "no lyrics"}
  340 |                 return primary
  345 |         return fallback
  349 |             return {"skipped": "dry-run"}
  351 |             return {"skipped": "RVC unavailable", "reason": "no installed RVC model/runtime"}
  354 |             return {"skipped": "no vocal"}
  357 |             return {"skipped": "no rvc_voice_name"}
  359 |         return render_rvc_vocal(
  373 |             return {"skipped": "no beat"}
  381 |                 return {"ok": True, "mix_path": mix_path, "vocal": False}
  395 |             return {"ok": True, "mix_path": mix_path, "vocal": True}
  397 |             return {"ok": False, "reason": str(e)}
  402 |             return {"skipped": "no mix"}
  405 |         return master_ai(mix, out_master, reference_wav=ws.get("reference_master_wav"),
  413 |         return render_cover_ai(title=title, artist=artist, genre=ws["genre"],
  418 |             return {"skipped": "no clap"}
  422 |             return {"skipped": "no master"}
  437 |             return {"ok": True, "tags": tags, "goal": ws["genre"],
  440 |             return {"ok": False, "reason": str(e)}
  470 |     return result
```

## `if` — 45 совпадений
```
   36 |         if generated.ndim == 1:
   42 |         if generated.shape[1] == 1:
   55 |         if speaker_wav and Path(speaker_wav).exists():
   59 |         if not target.exists() or target.stat().st_size <= 100:
   76 |         if synth_fn is None:
   80 |         if source is None or not source.exists():
   84 |         if source.resolve() != target.resolve():
  102 |         if not safe_voice_name:
  111 |         if source is None or not source.exists() or source.stat().st_size <= 100:
  115 |         if source.resolve() != target.resolve():
  147 |     if not out_root:
  163 |         if not artist_slug:
  170 |         if dry_run:
  175 |         if handle is not None:
  184 |         if not quality["ok"]:
  213 |         if dry_run:
  223 |         if not quality["ok"]:
  234 |         if dry_run:
  236 |         if handle is None:
  273 |                 if any(p.is_cuda for p in model.lm.parameters()):
  281 |         if full.shape[-1] > total:
  283 |         if full.ndim == 1:
  287 |             if full.shape[1] == 1:
  290 |         if peak > 0.99:
  302 |         if dry_run:
  304 |         if handle is None:
  315 |         if result.get("ok"):
  328 |         if dry_run:
  331 |         if not lyrics.strip():
  337 |         if handle is not None:
  339 |             if primary.get("ok"):
  348 |         if dry_run:
  350 |         if handle is None:
  353 |         if not vocal or not Path(vocal).exists():
  356 |         if not voice_name:
  372 |         if not beat or not Path(beat).exists():
  377 |             if b.ndim == 1:
  379 |             if not vocal or not Path(vocal).exists():
  383 |             if sr_v != sr_b:
  387 |             if v.ndim == 1:
  392 |             if peak > 0.99:
  401 |         if not mix:
  417 |         if bundle is None:
  421 |         if not Path(master).exists():
  431 |             if any(p.is_cuda for p in model.parameters()):
```

## `for` — 2 совпадений
```
  270 |         for i in range(1, n_chunks):
  433 |                           for k, v in inputs.items()}
```

## `with` — 1 совпадений
```
  434 |             with torch.no_grad():
```

## `np` — 8 совпадений
```
  279 |         full = np.concatenate(chunks, axis=-1)
  284 |             full = np.stack([full, full], axis=-1)
  288 |                 full = np.concatenate([full, full], axis=1)
  289 |         peak = float(np.max(np.abs(full)) + 1e-9)
  378 |                 b = np.stack([b, b], axis=-1)
  388 |                 v = np.stack([v, v], axis=-1)
  391 |             peak = float(np.max(np.abs(mix)) + 1e-9)
  436 |             tags = [cand[i] for i in np.argsort(-logits)[:5]]
```

## `sf` — 6 совпадений
```
   44 |         sf.write(out_path, generated.astype("float32"), int(getattr(handle, "sample_rate", 32000)),
  292 |         sf.write(out_path, full.astype("float32"), int(sr), subtype="PCM_16")
  376 |             b, sr_b = sf.read(beat)
  380 |                 sf.write(mix_path, b, sr_b)
  382 |             v, sr_v = sf.read(vocal)
  394 |             sf.write(mix_path, mix, sr_b)
```

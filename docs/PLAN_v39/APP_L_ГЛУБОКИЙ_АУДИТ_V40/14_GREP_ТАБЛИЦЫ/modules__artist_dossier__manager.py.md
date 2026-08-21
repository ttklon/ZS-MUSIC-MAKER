# grep-таблицы `modules/artist_dossier/manager.py`

## `import` — 15 совпадений
```
    4 | from __future__ import annotations
    5 | import json, re, time, hashlib, shutil
    6 | from dataclasses import dataclass, field, asdict
    7 | from pathlib import Path
    8 | from typing import Any, Dict, List, Optional
    9 | from app.ai.registry import registry
   10 | from app.ai.sequential_runner import SequentialAIRunner, AIStage
   11 | from app.ai import prompts as P
   12 | from app.ai import llm_service as LLM
   13 | from app.ai.quality import (
   44 |     import numpy as np
  194 |                 import torchaudio, soundfile as sf
  195 |                 from demucs.apply import apply_model
  243 |                     import librosa, numpy as np
  264 |                 import torch, librosa, numpy as np
```

## `except` — 6 совпадений
```
   79 |     except Exception as exc:
  145 |             except Exception:
  174 |             except Exception as e:
  219 |             except Exception as e:
  252 |                 except Exception as e:
  278 |             except Exception as e:
```

## `try` — 6 совпадений
```
   54 |     try:
  142 |             try:
  172 |             try:
  193 |             try:
  242 |                 try:
  262 |             try:
```

## `def` — 24 совпадений
```
   24 | def _slug(name: str) -> str:
   29 | def _track_id(title: str, url: str = "") -> str:
   34 | def resolve_vocal_source_index(model: Any) -> int:
   42 | def rank_clap_tags(candidates: list[str], logits: Any, limit: int = 6) -> list[str]:
   52 | def transcribe_reference_audio(model: Any, audio_path: str, output_path: str) -> dict:
  108 |     def __init__(self, root: Optional[Path] = None):
  112 |     def add_artist(self, artist: str,
  131 |     def add_track(self, artist: str, title: str,
  158 |     def build_full_dossier(self, artist: str, refresh: bool = False,
  183 |     def _analyze_single_track(self, slug: str, tr: TrackEntry, progress_cb=None) -> None:
  188 |         def _demucs_stage(model, ctx):
  223 |         def _asr_stage(model, ctx):
  239 |         def _features_stage(_, ctx):
  257 |         def _tag_stage(bundle, ctx):
  282 |         def _llm_stage(handle, ctx):
  316 |     def _aggregate_artist_dossier(self, slug: str, a: ArtistEntry) -> Dict[str, Any]:
  344 |     def get_artist_dossier(self, artist: str) -> Optional[Dict[str, Any]]:
  348 |     def get_track_dossier(self, artist: str, track_id: str) -> Optional[Dict[str, Any]]:
  352 |     def list_artists(self) -> List[Dict[str, Any]]:
  363 |     def list_tracks(self, artist: str) -> List[Dict[str, Any]]:
  378 |     def _save_artist(self, a: ArtistEntry) -> None:
  383 |     def _load_artist(self, slug: str) -> Optional[ArtistEntry]:
  389 |     def _save_track(self, slug: str, tr: TrackEntry) -> None:
  394 |     def _load_track(self, slug: str, tid: str) -> Optional[TrackEntry]:
```

## `class` — 3 совпадений
```
   84 | class TrackEntry:
   98 | class ArtistEntry:
  107 | class DossierManager:
```

## `raise` — 3 совпадений
```
   38 |         raise ValueError("Demucs model does not expose a 'vocals' source")
   48 |         raise ValueError("CLAP scores do not match the candidate vocabulary")
  163 |             raise ValueError(f"Artist {artist} not registered")
```

## `return` — 39 совпадений
```
   26 |     return s.lower() or "unknown"
   31 |     return _slug(title)[:32] + "_" + hashlib.md5(base.encode("utf-8")).hexdigest()[:8]
   39 |     return sources.index("vocals")
   49 |     return [candidates[index] for index in np.argsort(-scores)[:max(1, limit)]]
   61 |             return {
   70 |         return {
   80 |         return {"ok": False, "reason": f"ASR transcription failed: {exc}"}
  129 |         return entry
  156 |         return entry
  181 |         return a.dossier
  190 |                 return {"skipped": "stem_splitter unavailable"}
  192 |                 return {"skipped": "no audio"}
  212 |                 return {
  220 |                 return {"ok": False, "error": str(e)}
  225 |                 return {"lyrics": tr.lyrics, "source": "user"}
  227 |                 return {"skipped": "asr unavailable"}
  231 |                 return {"skipped": "no audio for ASR"}
  232 |             return transcribe_reference_audio(
  254 |             return feats
  259 |                 return {"skipped": "audio_tagger unavailable"}
  261 |                 return {"skipped": "no audio"}
  277 |                 return {"ok": True, "tags": rank_clap_tags(cand, logits), "source": "clap"}
  279 |                 return {"ok": False, "error": str(e)}
  285 |                 return {"skipped": "no lyrics"}
  293 |                 return {"error": quality["reason"], "quality": quality}
  295 |             return js
  323 |             return {"note": "no lyrics collected - cannot build dossier"}
  326 |             return {"note": "analysis_llm unavailable - dossier deferred",
  334 |             return {
  342 |         return js
  346 |         return a.dossier if a else None
  350 |         return tr.dossier if tr else None
  361 |         return out
  367 |             return []
  376 |         return out
  386 |             return None
  387 |         return ArtistEntry(**json.loads(p.read_text(encoding="utf-8")))
  397 |             return None
  398 |         return TrackEntry(**json.loads(p.read_text(encoding="utf-8")))
```

## `if` — 39 совпадений
```
   37 |     if "vocals" not in sources:
   47 |     if len(scores) != len(candidates):
   60 |         if not quality["ok"]:
  140 |         if audio_path and Path(audio_path).exists():
  147 |         if lyrics:
  152 |         if tid not in a.tracks:
  162 |         if not a:
  166 |             if not tr:
  168 |             if not refresh and tr.status == "analyzed":
  169 |                 if progress_cb:
  184 |         if progress_cb:
  189 |             if model is None:
  191 |             if not tr.audio_path or not Path(tr.audio_path).exists():
  197 |                 if wav.dim() == 1:
  199 |                 if wav.shape[0] == 1:
  203 |                 if dev.startswith("cuda"):
  224 |             if tr.lyrics:
  226 |             if model is None:
  230 |             if not src or not Path(src).exists():
  241 |             if tr.audio_path and Path(tr.audio_path).exists():
  258 |             if bundle is None:
  260 |             if not tr.audio_path or not Path(tr.audio_path).exists():
  272 |                 if any(p.is_cuda for p in model.parameters()):
  284 |             if not lyrics.strip():
  292 |             if not quality["ok"]:
  301 |         if (sink.get("tags") or {}).get("tags"):
  303 |         if (sink.get("asr") or {}).get("lyrics") and not tr.lyrics:
  306 |         if isinstance(br, dict) and "error" not in br and "skipped" not in br:
  313 |         if progress_cb:
  320 |             if tr and tr.lyrics and tr.lyrics.strip():
  322 |         if not chunks:
  325 |         if not registry.is_available("analysis_llm"):
  333 |         if not quality["ok"]:
  355 |             if not adir.is_dir():
  358 |             if a:
  366 |         if not a:
  371 |             if tr:
  385 |         if not p.exists():
  396 |         if not p.exists():
```

## `for` — 7 совпадений
```
  116 |         for sub in ("tracks", "audio", "vocals", "lyrics"):
  121 |         for t in tracks or []:
  164 |         for tid in a.tracks:
  274 |                               for k, v in inputs.items()}
  318 |         for tid in a.tracks:
  354 |         for adir in sorted(self.root.iterdir()):
  369 |         for tid in a.tracks:
```

## `with` — 2 совпадений
```
  275 |                 with torch.no_grad():
  328 |         with registry.use("analysis_llm") as m:
```

## `np` — 4 совпадений
```
   46 |     scores = np.asarray(logits).reshape(-1)
   49 |     return [candidates[index] for index in np.argsort(-scores)[:max(1, limit)]]
  249 |                     feats["key"] = keys[int(np.argmax(chroma))]
  251 |                     feats["loudness_rms"] = float(np.sqrt(np.mean(y ** 2)) + 1e-9)
```

## `sf` — 1 совпадений
```
  210 |                 sf.write(str(out), vocals, int(sr))
```

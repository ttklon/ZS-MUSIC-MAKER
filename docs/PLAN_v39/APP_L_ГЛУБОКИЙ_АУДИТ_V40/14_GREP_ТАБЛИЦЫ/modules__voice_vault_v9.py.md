# grep-таблицы `modules/voice_vault_v9.py`

## `import` — 12 совпадений
```
   21 | from __future__ import annotations
   23 | import hashlib
   24 | import json
   25 | import math
   26 | import shutil
   27 | import time
   28 | from pathlib import Path
   31 |     import numpy as np
   36 |     import soundfile as sf
  130 |         from faster_whisper import WhisperModel
  138 |         import whisper
  292 |             from modules import rvc_trainer_v9 as rvc_trainer
```

## `print` — 1 совпадений
```
  314 |     print(json.dumps(clean_stats(), ensure_ascii=False, indent=2))
```

## `except` — 10 совпадений
```
   32 | except Exception:
   39 | except Exception:
   44 | except Exception:
   73 |         except Exception:
  114 |     except Exception as e:
  135 |     except Exception:
  142 |     except Exception:
  191 |         except Exception as e:
  293 |         except Exception as e:
  303 |     except Exception as e:
```

## `try` — 10 совпадений
```
   30 | try:
   35 | try:
   42 | try:
   71 |         try:
   95 |     try:
  129 |     try:
  137 |     try:
  189 |         try:
  291 |         try:
  300 |     try:
```

## `def` — 12 совпадений
```
   69 | def _load_index() -> dict:
   78 | def _save_index(idx: dict) -> None:
   84 | def _md5(path: Path, limit: int = 1 << 20) -> str:
   92 | def _snr_and_clipping(path: Path) -> dict:
  118 | def _guess_style(features: dict, hint: str | None = None) -> str:
  128 | def _transcribe(path: Path) -> str | None:
  147 | def calculate_phoneme_coverage(text: str) -> dict:
  170 | def add_recording(
  217 | def list_recordings(style: str | None = None) -> list[dict]:
  225 | def clean_stats() -> dict:
  257 | def export_manifest_for_rvc(out_path: str | None = None) -> str:
  285 | def maybe_trigger_retrain(rvc_trainer=None) -> dict:
```

## `return` — 27 совпадений
```
   72 |             return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
   74 |             return {"items": {}}
   75 |     return {"items": {}}
   88 |     return h.hexdigest()
   94 |         return {"snr_db": None, "clip_ratio": None, "duration_s": None}
  104 |             return {"snr_db": None, "clip_ratio": None, "duration_s": dur}
  109 |         return {
  115 |         return {"snr_db": None, "clip_ratio": None, "duration_s": None, "err": str(e)}
  120 |         return hint
  123 |         return "adlib"
  124 |     return "rap"  # безопасный дефолт
  134 |         return " ".join(s.text.strip() for s in segs)[:500]
  141 |         return (m.transcribe(str(path)).get("text") or "")[:500]
  144 |     return None
  150 |         return {}
  158 |     return {
  178 |         return {"ok": False, "error": f"not found: {src_path}"}
  185 |         return {"ok": True, "already_indexed": True, "item": items[mid]}
  192 |             return {"ok": False, "error": f"copy failed: {e}"}
  214 |     return {"ok": True, "already_indexed": False, "item": entry}
  222 |     return items
  246 |     return {
  282 |     return str(dst)
  288 |         return {"triggered": False, "reason": "not enough clean voice", "stats": stats}
  294 |             return {
  302 |         return {"triggered": True, "manifest": manifest, "stats": stats, "job": job}
  304 |         return {
```

## `if` — 17 совпадений
```
   70 |     if INDEX_FILE.exists():
   93 |     if not HAS_SF or np is None:
   97 |         if hasattr(y, "ndim") and y.ndim > 1:
  103 |         if len(rmss) < 20:
  119 |     if hint and hint in STYLES:
  122 |     if dur < 2.0:
  149 |     if not text:
  177 |     if not p.exists():
  184 |     if mid in items and not overwrite:
  188 |     if not dst.exists():
  220 |     if style:
  237 |         if (snr is None or snr >= 15.0) and (clip is None or clip < 0.01):
  241 |         if x.get("transcript"):
  264 |         if (snr is None or snr >= 15.0) and (clip is None or clip < 0.01):
  287 |     if not stats["ready_for_retrain"]:
  290 |     if rvc_trainer is None:
  313 | if __name__ == "__main__":
```

## `for` — 2 совпадений
```
  232 |     for x in items:
  260 |     for x in idx.get("items", {}).values():
```

## `with` — 1 совпадений
```
   86 |     with open(path, "rb") as f:
```

## `open` — 1 совпадений
```
   86 |     with open(path, "rb") as f:
```

## `np` — 4 совпадений
```
  102 |         rmss = sorted([float(np.sqrt(np.mean(np.square(c)) + 1e-12)) for c in chunks])
  105 |         noise = float(np.mean(rmss[: max(1, len(rmss) // 20)]))
  106 |         signal = float(np.mean(rmss[-max(1, len(rmss) // 5) :]))
  108 |         clip = float(np.mean(np.abs(y) > 0.98))
```

## `sf` — 1 совпадений
```
   96 |         y, sr = sf.read(str(path), always_2d=False)
```

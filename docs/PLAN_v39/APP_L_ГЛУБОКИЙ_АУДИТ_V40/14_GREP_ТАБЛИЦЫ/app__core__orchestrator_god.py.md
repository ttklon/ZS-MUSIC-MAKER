# grep-таблицы `app/core/orchestrator_god.py`

## `import` — 10 совпадений
```
    9 | import os
   10 | import json
   11 | from pathlib import Path
   12 | from typing import Any, Optional
   14 | from app.core.pipeline_core import ZSPipeline, PipelineContext
   15 | from modules import (
   34 |         import numpy as _np
  116 |                 from modules.chanson_engine import ChansonEngine
  120 |                 from modules.cyber_synth import CyberSynth
  154 |                 from modules import lyrics_gen, voice_synth
```

## `print` — 3 совпадений
```
  128 |             print(f"[orchestrator_god] Engine fallback due to: {e}")
  180 |                 print("[orchestrator_god] vocal synth BLOCKED: no TTS engine available — pipeline продолжает без вокала")
  182 |                 print(f"[orchestrator_god] Auto-vocal synthesis error: {e}")
```

## `except` — 3 совпадений
```
   37 |     except ImportError:
  127 |         except Exception as e:
  181 |             except Exception as e:
```

## `try` — 3 совпадений
```
   33 |     try:
  114 |         try:
  153 |             try:
```

## `def` — 8 совпадений
```
   24 | def _json_safe(obj: Any) -> Any:
   48 | def _save_project_meta(project_id: str, data: dict, out_root: Path):
   53 | def run_god_pipeline(
   84 |     def stage_arr(ctx: PipelineContext):
   96 |     def stage_midi(ctx: PipelineContext):
  108 |     def stage_audio(ctx: PipelineContext):
  142 |     def stage_vocal(ctx: PipelineContext):
  191 |     def stage_master(ctx: PipelineContext):
```

## `return` — 14 совпадений
```
   36 |             return obj.item()
   40 |         return {str(k): _json_safe(v) for k, v in obj.items()}
   42 |         return [_json_safe(v) for v in obj]
   44 |         return str(obj)
   45 |     return obj
   91 |         return arranger.get_structure(state["tags"])
   99 |         return {
  126 |                 return out_name
  137 |         return res
  150 |             return clean_vocal_wav
  177 |                     return vocal_draft
  186 |         return None
  197 |         return mastering_pro.process_mastering(beat_wav, master_wav, vocal_path=vocal_wav, target_lufs=-12.0)
  232 |     return res
```

## `if` — 10 совпадений
```
   35 |         if isinstance(obj, _np.generic):
   39 |     if isinstance(obj, dict):
   41 |     if isinstance(obj, (list, tuple, set)):
   43 |     if isinstance(obj, Path):
   69 |     if not isinstance(wizard_state, dict):
   73 |     if out_root is None:
  115 |             if "chanson" in genre_name.lower() or "шансон" in genre_name.lower():
  124 |             if res.get("ok"):
  146 |         if vocal_wav and os.path.exists(vocal_wav):
  174 |                 if synth_path and os.path.exists(synth_path):
```

## `for` — 1 совпадений
```
  209 |     for name, sres in final_out["results"].items():
```

## `with` — 1 совпадений
```
   50 |     with open(meta_path, "w", encoding="utf-8") as f:
```

## `open` — 1 совпадений
```
   50 |     with open(meta_path, "w", encoding="utf-8") as f:
```

## `np` — 1 совпадений
```
   28 |     строки вида 'np.float32(0.95)' — метрики в project_meta.json переставали
```

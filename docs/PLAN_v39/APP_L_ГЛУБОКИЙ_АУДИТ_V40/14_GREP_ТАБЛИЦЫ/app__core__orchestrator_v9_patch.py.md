# grep-таблицы `app/core/orchestrator_v9_patch.py`

## `import` — 16 совпадений
```
   22 | from __future__ import annotations
   24 | import json
   25 | import time
   26 | import traceback
   27 | from pathlib import Path
   48 |         from modules.reference_ingest import build_style_vector
   66 |         from modules.arrangement_engine import build_arrangement
   87 |         from agents.sample_hunter_v9 import save_manifest, unified_search
  105 |         from app.core.orchestrator_v8_patch import run_pipeline_v8
  117 |         from modules.voice_vault_v9 import maybe_trigger_retrain
  131 |             from modules.anti_ai_polish import polish_track
  155 |         from modules.mastering_v9 import render_all_stands
  174 |         from modules.hit_scorer import score_track
  192 |         from modules.tiktok_edit_v9 import make_all_cuts
  210 |         from modules.release_pack_v9 import build_release_v9
  216 |             from modules.voice_vault_v9 import export_manifest_for_rvc
```

## `except` — 12 совпадений
```
   34 |     except Exception:
   59 |     except Exception as e:
   80 |     except Exception as e:
   98 |     except Exception as e:
  108 |     except Exception as e:
  123 |     except Exception as e:
  145 |         except Exception as e:
  167 |     except Exception as e:
  185 |     except Exception as e:
  204 |     except Exception as e:
  222 |         except Exception:
  249 |     except Exception as e:
```

## `try` — 12 совпадений
```
   31 |     try:
   47 |     try:
   65 |     try:
   86 |     try:
  104 |     try:
  116 |     try:
  130 |         try:
  154 |     try:
  173 |     try:
  191 |     try:
  209 |     try:
  215 |         try:
```

## `def` — 4 совпадений
```
   30 | def _stage(hook, name: str, progress: float):
   38 | def run_pipeline_v9(orch, recipe: dict, stage_hook=None):
  273 | def apply(orch) -> None:
  280 |     def _wrapper(recipe, stage_hook=None):
```

## `return` — 2 совпадений
```
  270 |     return result
  281 |         return run_pipeline_v9(orch, recipe, stage_hook=stage_hook)
```

## `if` — 12 совпадений
```
   32 |         if callable(hook):
   52 |         if refs:
  121 |         if rv.get("triggered"):
  128 |     if master_wav and Path(master_wav).exists():
  142 |             if not polish_r.get("ok"):
  157 |         if polished_wav and Path(polished_wav).exists():
  164 |                 if r.get("ok"):
  177 |         if target_for_score and Path(target_for_score).exists():
  195 |         if src and Path(src).exists():
  201 |                 if r.get("ok"):
  275 |     if not hasattr(orch, "_run_pipeline_v8"):
  277 |         if original:
```

## `for` — 2 совпадений
```
  162 |             for name in ("car", "club", "streaming"):
  200 |             for name, r in tres.get("results", {}).items():
```

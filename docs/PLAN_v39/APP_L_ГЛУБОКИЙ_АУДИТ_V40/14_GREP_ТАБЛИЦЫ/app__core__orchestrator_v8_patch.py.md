# grep-таблицы `app/core/orchestrator_v8_patch.py`

## `import` — 6 совпадений
```
   16 | from __future__ import annotations
   18 | import traceback
   19 | from pathlib import Path
   40 |         from modules.lyrics_gen_v8 import generate_lyrics_v8
   78 |             from modules.female_backing import (
  101 |             from modules.auto_qa import audit_track, should_retry
```

## `except` — 5 совпадений
```
   26 |     except Exception:
   58 |     except Exception as e:
   70 |         except Exception as e:
   93 |         except Exception as e:
  120 |         except Exception as e:
```

## `try` — 5 совпадений
```
   23 |     try:
   39 |     try:
   68 |         try:
   77 |         try:
  100 |         try:
```

## `def` — 3 совпадений
```
   22 | def _stage(hook, name: str, progress: float):
   30 | def run_pipeline_v8(orch, recipe: dict, stage_hook=None):
  127 | def apply(orch):
```

## `return` — 3 совпадений
```
  119 |                     return run_pipeline_v8(orch, recipe, stage_hook)
  124 |     return result
  130 |         return
```

## `if` — 8 совпадений
```
   24 |         if callable(hook):
   64 |     if hasattr(orch, "_run_pipeline_v7"):
   75 |     if recipe.get("female_backing") and result.get("vocal_wav"):
   98 |     if master_path and Path(master_path).exists():
  108 |             if recipe.get("auto_qa_loop", False):
  114 |                 if retry:
  129 |     if hasattr(orch, "_v8_applied"):
  131 |     if hasattr(orch, "run_pipeline"):
```

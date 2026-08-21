# grep-таблицы `app/core/orchestrator_v11_patch.py`

## `import` — 10 совпадений
```
    8 | from __future__ import annotations
   10 | import json
   11 | import os
   12 | import sys
   13 | import time
   14 | import traceback
   15 | from pathlib import Path
  328 |     import struct
  329 |     import wave
  378 |     import tempfile
```

## `print` — 2 совпадений
```
   23 |         print(msg)
  401 |     print("orchestrator_v11_patch self-test:", "OK" if _self_test() else "FAIL")
```

## `except` — 15 совпадений
```
   24 |     except UnicodeEncodeError:
   38 |         except Exception as e:
   47 |         except Exception as e:
   65 |             except Exception:
   88 |     except Exception as e:
  108 |         except Exception as e:
  128 |             except TypeError:
  134 |                 except Exception as e2:
  146 |     except Exception as e:
  184 |         except Exception as e:
  243 |         except Exception as e:
  270 |         except Exception as e:
  300 |     except Exception as e:
  339 |         except Exception:
  371 |         except Exception as e:
```

## `try` — 15 совпадений
```
   22 |     try:
   36 |         try:
   45 |         try:
   63 |             try:
   74 |     try:
  100 |         try:
  116 |     try:
  119 |             try:
  129 |                 try:
  159 |         try:
  194 |         try:
  253 |         try:
  297 |     try:
  333 |         try:
  368 |         try:
```

## `def` — 7 совпадений
```
   21 | def _safe_print(msg):
   28 | def _load_deps():
   52 | def run_full_pipeline_v11(
   60 |     def prog(stage, pct, msg=""):
  324 | def _minimal_pipeline_fallback(project_id, wizard_state, release_dir, prog):
  365 | def register(app_ctx=None):
  377 | def _self_test():
```

## `return` — 5 совпадений
```
   49 |     return deps
  309 |     return {
  345 |     return {
  374 |     return ok
  395 |         return os.path.exists(res["release_dir"]) and os.path.exists(
```

## `if` — 21 совпадений
```
   62 |         if progress_cb:
   75 |         if "hw" in deps:
   78 |                 if hasattr(deps["hw"], m):
   81 |             if isinstance(probe, dict):
   83 |                 if (
   94 |     if "kpi" in deps:
   99 |     if expert_config and "expert" in deps:
  103 |             if v["errors"]:
  117 |         if "v10_patch" in deps and hasattr(deps["v10_patch"], "full_v10_pipeline"):
  144 |         if st:
  151 |         if st:
  157 |     if "video_edit" in deps:
  182 |             if st:
  186 |             if st:
  192 |     if "dist" in deps:
  241 |             if st:
  245 |             if st:
  252 |     if kpi_session and "kpi" in deps:
  332 |     if not os.path.exists(p):
  342 |     if not os.path.exists(lp):
  400 | if __name__ == "__main__":
```

## `for` — 5 совпадений
```
   30 |     for name, path in [
   40 |     for name, path in [
   77 |             for m in ("detect_hardware", "detect"):
  285 |             for k, v in (v10_out or {}).items()
  367 |     for m in REGISTERED_MODULES_V11:
```

## `with` — 5 совпадений
```
  265 |             with open(
  298 |         with open(manifest_path, "w", encoding="utf-8") as f:
  334 |             with wave.open(p, "wb") as wf:
  343 |         with open(lp, "w", encoding="utf-8") as f:
  380 |     with tempfile.TemporaryDirectory() as tmp:
```

## `open` — 4 совпадений
```
  265 |             with open(
  298 |         with open(manifest_path, "w", encoding="utf-8") as f:
  334 |             with wave.open(p, "wb") as wf:
  343 |         with open(lp, "w", encoding="utf-8") as f:
```

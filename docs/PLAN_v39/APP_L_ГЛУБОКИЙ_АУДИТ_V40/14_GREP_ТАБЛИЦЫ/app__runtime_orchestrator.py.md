# grep-таблицы `app/runtime_orchestrator.py`

## `import` — 8 совпадений
```
    1 | from __future__ import annotations
    3 | import threading
    4 | import time
    5 | import uuid
    6 | from dataclasses import dataclass, field
    7 | from pathlib import Path
    8 | from typing import Any
   10 | from app.core.orchestrator import run_full_pipeline
```

## `print` — 1 совпадений
```
   44 |                 print(msg)
```

## `except` — 2 совпадений
```
   45 |         except Exception:
  143 |         except Exception as e:
```

## `try` — 2 совпадений
```
   40 |         try:
   89 |         try:
```

## `def` — 7 совпадений
```
   30 |     def __init__(self, log=None):
   39 |     def _log(self, msg: str):
   48 |     def _ensure_worker(self):
   55 |     def enqueue(self, recipe: dict[str, Any]) -> str:
   66 |     def enqueue_batch(self, recipes: list[dict[str, Any]]) -> list[str]:
   69 |     def _run_loop(self):
   82 |     def _process(self, job: Job):
```

## `class` — 2 совпадений
```
   16 | class Job:
   29 | class RuntimeOrchestrator:
```

## `return` — 3 совпадений
```
   50 |             return
   64 |         return tid
   67 |         return [self.enqueue(r) for r in (recipes or [])]
```

## `if` — 9 совпадений
```
   41 |             if self.log is not None and hasattr(self.log, "info"):
   49 |         if self._worker and self._worker.is_alive():
   73 |                 if self._queue:
   75 |             if not tid:
   79 |             if job:
  101 |                 if name == "_stage_release_pack":
  117 |                 if isinstance(a, str) and a.strip()
  122 |                 if isinstance(w, str) and w.strip()
  141 |             if job.status == "error":
```

## `for` — 3 совпадений
```
   98 |             for st in stages:
  116 |                 for a in (hit.get("actions") or [])[:4]
  121 |                 for w in (res.get("warnings") or [])[:4]
```

## `while` — 1 совпадений
```
   70 |         while not self._stop.is_set():
```

## `with` — 2 совпадений
```
   59 |         with self._lock:
   72 |             with self._lock:
```

## `sleep` — 1 совпадений
```
   76 |                 time.sleep(0.2)
```

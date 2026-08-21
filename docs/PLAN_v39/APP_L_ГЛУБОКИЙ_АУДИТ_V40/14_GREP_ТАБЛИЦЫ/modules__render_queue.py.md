# grep-таблицы `modules/render_queue.py`

## `import` — 11 совпадений
```
   11 | from __future__ import annotations
   13 | import json
   14 | import threading
   15 | import time
   16 | import uuid
   17 | from collections.abc import Callable
   18 | from dataclasses import asdict, dataclass, field
   19 | from pathlib import Path
  157 |                 from app.core.orchestrator import Orchestrator
  158 |                 from app.hw_probe import probe_hw
  159 |                 from app.logger import make_logger
```

## `print` — 1 совпадений
```
  197 |     print(json.dumps(q.status_summary(), indent=2))
```

## `except` — 2 совпадений
```
   48 |         except Exception:
  172 |         except Exception as e:
```

## `try` — 2 совпадений
```
   46 |         try:
  154 |         try:
```

## `def` — 19 совпадений
```
   40 |     def to_dict(self):
   44 | def _load_state() -> list[dict]:
   53 | def _save_state(items: list[QueueItem]) -> None:
   66 |     def __init__(self, orchestrator=None, log: Callable[[str], None] = print):
   75 |     def _restore(self):
   85 |     def _persist(self):
   89 |     def enqueue(self, recipe: dict) -> str:
   96 |     def enqueue_batch(self, recipes: list[dict]) -> list[str]:
   99 |     def status_summary(self) -> dict:
  106 |     def list_items(self) -> list[dict]:
  109 |     def cancel(self, item_id: str) -> bool:
  118 |     def clear_done(self):
  123 |     def start(self):
  131 |     def stop(self):
  135 |     def _run_loop(self):
  143 |     def _pick_next(self) -> QueueItem | None:
  150 |     def _process(self, item: QueueItem):
  163 |             def on_stage(stage: str, progress: float):
  181 |     def morning_report(self) -> dict:
```

## `class` — 2 совпадений
```
   28 | class QueueItem:
   60 | class RenderQueue:
```

## `return` — 14 совпадений
```
   41 |         return asdict(self)
   47 |             return json.loads(STATE_FILE.read_text(encoding="utf-8"))
   49 |             return []
   50 |     return []
   94 |         return item.id
   97 |         return [self.enqueue(r) for r in recipes]
  104 |         return c
  107 |         return [i.to_dict() for i in self.items]
  115 |                 return True
  116 |         return False
  125 |             return
  146 |                 return it
  147 |         return None
  185 |         return {
```

## `if` — 8 совпадений
```
   45 |     if STATE_FILE.exists():
   78 |             if d.get("status") == "running":
  111 |             if it.id == item_id and it.status == "pending":
  124 |         if self._worker and self._worker.is_alive():
  138 |             if not next_item:
  145 |             if it.status == "pending":
  155 |             if self.orchestrator is None:
  195 | if __name__ == "__main__":
```

## `for` — 4 совпадений
```
   76 |         for d in _load_state():
  101 |         for it in self.items:
  110 |         for it in self.items:
  144 |         for it in self.items:
```

## `while` — 1 совпадений
```
  136 |         while not self._stop.is_set():
```

## `sleep` — 1 совпадений
```
  139 |                 time.sleep(3)
```

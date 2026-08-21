# grep-таблицы `app/ai/sequential_runner.py`

## `import` — 5 совпадений
```
    4 | from __future__ import annotations
    5 | import gc, time, logging
    6 | from dataclasses import dataclass, field
    7 | from typing import Any, Callable, Dict, List, Optional
    8 | from app.ai.registry import registry, MODEL_REGISTRY
```

## `except` — 1 совпадений
```
  110 |             except Exception as e:
```

## `try` — 1 совпадений
```
   71 |             try:
```

## `def` — 6 совпадений
```
   43 |     def to_dict(self) -> Dict[str, Any]:
   52 |     def __init__(self):
   56 |     def add(self, stage: AIStage) -> "SequentialAIRunner":
   60 |     def sink(self) -> Dict[str, Any]:
   63 |     def run(self, context: Optional[Dict[str, Any]] = None) -> RunReport:
  124 | def _summarize(out: Any) -> str:
```

## `class` — 4 совпадений
```
   17 | class AIStage:
   27 | class StageReport:
   39 | class RunReport:
   51 | class SequentialAIRunner:
```

## `raise` — 1 совпадений
```
   81 |                     raise KeyError(f"Model role '{st.model}' not in registry")
```

## `return` — 9 совпадений
```
   44 |         return {"total_sec": round(self.total_sec, 2),
   58 |         return self
   61 |         return self._sink
  121 |         return report
  126 |         return ""
  129 |         return s if len(s) < 200 else s[:200] + "..."
  131 |         return f"dict(keys={list(out.keys())[:6]})"
  133 |         return f"{type(out).__name__}(len={len(out)})"
  134 |     return type(out).__name__
```

## `if` — 11 совпадений
```
   11 | if not logger.handlers:
   72 |                 if st.model is None:
   80 |                 if st.model not in MODEL_REGISTRY:
   82 |                 if not registry.is_available(st.model):
   84 |                     if st.optional and st.fallback_fn:
   93 |                     if st.optional:
  116 |                 if st.unload_after:
  125 |     if out is None:
  127 |     if isinstance(out, (str, int, float, bool)):
  130 |     if isinstance(out, dict):
  132 |     if isinstance(out, (list, tuple)):
```

## `for` — 1 совпадений
```
   68 |         for st in self.stages:
```

# grep-таблицы `app/core/orchestrator_async.py`

## `import` — 9 совпадений
```
    9 | import asyncio
   10 | import time
   11 | import os
   12 | import json
   13 | from pathlib import Path
   14 | from typing import Any, List, Optional, Callable
   15 | from dataclasses import dataclass, asdict
   50 |         import multiprocessing
   60 |         from modules import beat_constructor, phonk_engine, voice_cleaner, mastering_pro
```

## `print` — 1 совпадений
```
  115 |     print(f"Async Pipeline Done in {res['duration_sec']}s")
```

## `except` — 1 совпадений
```
   37 |     except Exception as e:
```

## `try` — 1 совпадений
```
   28 |     try:
```

## `def` — 5 совпадений
```
   25 | async def run_stage_async(name: str, coro: Callable) -> AsyncStage:
   44 |     def __init__(self, project_id: str, out_root: Path):
   53 |     async def _run_limited(self, name: str, coro: Callable):
   57 |     async def run_pipeline(self, wizard_state: dict):
  112 | async def main_async():
```

## `class` — 2 совпадений
```
   18 | class AsyncStage:
   43 | class AsyncOrchestrator:
```

## `return` — 3 совпадений
```
   41 |     return stage
   55 |             return await run_stage_async(name, coro)
  110 |         return final_res
```

## `if` — 4 совпадений
```
   30 |         if asyncio.iscoroutinefunction(coro):
   79 |         if vocal_in and os.path.exists(vocal_in):
   89 |         if beat_stage and beat_stage.ok:
  117 | if __name__ == "__main__":
```

## `with` — 1 совпадений
```
  107 |         with open(self.out_root / "async_meta.json", "w") as f:
```

## `open` — 1 совпадений
```
  107 |         with open(self.out_root / "async_meta.json", "w") as f:
```

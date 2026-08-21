# grep-таблицы `app/core/pipeline_core.py`

## `import` — 8 совпадений
```
    9 | import time
   10 | import logging
   11 | import gc
   12 | import json
   13 | import os
   14 | from pathlib import Path
   15 | from typing import Dict, Any, List, Callable, Optional
   16 | from dataclasses import dataclass, field
```

## `except` — 4 совпадений
```
   52 |         except Exception as e:
   96 |         except Exception as e:
  116 |                 except Exception:
  129 |                     except Exception as e:
```

## `try` — 4 совпадений
```
   45 |         try:
   89 |         try:
  114 |                 try:
  122 |                     try:
```

## `def` — 6 совпадений
```
   38 |     def __init__(self, name: str, func: Callable[[PipelineContext], Any]):
   42 |     def execute(self, context: PipelineContext) -> StageResult:
   61 |     def __init__(
   82 |     def add_stage(self, name: str, func: Callable[[PipelineContext], Any]):
   86 |     def _save_checkpoint(self, stage_name: str, result: StageResult):
  103 |     def run(self, use_checkpoints: bool = True) -> Dict[str, Any]:
```

## `class` — 4 совпадений
```
   23 | class StageResult:
   31 | class PipelineContext:
   37 | class PipelineStage:
   60 | class ZSPipeline:
```

## `return` — 4 совпадений
```
   51 |             return res
   58 |             return res
   84 |         return self
  142 |         return {
```

## `if` — 6 совпадений
```
   77 |             if checkpoint_dir is not None
  107 |         if os.environ.get("ZSMM_NO_CHECKPOINTS") == "1":
  113 |             if use_checkpoints and cp_path.exists():
  118 |                 if age > self.CHECKPOINT_TTL_SEC:
  127 |                         if not res.ok: break
  138 |             if not res.ok:
```

## `for` — 1 совпадений
```
  110 |         for stage in self.stages:
```

## `with` — 2 совпадений
```
   90 |             with open(cp_path, "w", encoding="utf-8") as f:
  123 |                         with open(cp_path, "r", encoding="utf-8") as f:
```

## `open` — 2 совпадений
```
   90 |             with open(cp_path, "w", encoding="utf-8") as f:
  123 |                         with open(cp_path, "r", encoding="utf-8") as f:
```

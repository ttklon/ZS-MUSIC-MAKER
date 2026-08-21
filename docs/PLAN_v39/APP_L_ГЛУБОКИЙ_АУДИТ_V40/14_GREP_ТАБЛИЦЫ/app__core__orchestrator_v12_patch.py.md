# grep-таблицы `app/core/orchestrator_v12_patch.py`

## `import` — 11 совпадений
```
   17 | from __future__ import annotations
   19 | import sys
   20 | import time
   21 | import traceback
   22 | from collections.abc import Callable
   23 | from pathlib import Path
   24 | from typing import Any
   66 |         from modules import health_v12
   81 |         from modules import master_pipeline_v12 as mp
   99 |             from app.core import orchestrator_v11_patch as v11
  122 |         from modules import kpi_dashboard_v12 as kd
```

## `print` — 1 совпадений
```
   33 |         print(msg)
```

## `except` — 5 совпадений
```
   34 |     except UnicodeEncodeError:
   75 |     except Exception as e:  # noqa: BLE001
   92 |     except Exception as e:  # noqa: BLE001
  115 |         except Exception as e:  # noqa: BLE001
  130 |     except Exception as e:  # noqa: BLE001
```

## `try` — 5 совпадений
```
   32 |     try:
   65 |     try:
   80 |     try:
   98 |         try:
  121 |     try:
```

## `def` — 3 совпадений
```
   31 | def _safe_print(msg: str) -> None:
   38 | def run_full_pipeline_v12(
  137 | def register() -> str:
```

## `return` — 2 совпадений
```
  134 |     return result
  139 |     return "orchestrator_v12_patch:ready"
```

## `if` — 5 совпадений
```
   27 | if str(ROOT) not in sys.path:
   97 |     if not master_ok:
  101 |             if hasattr(v11, "run_full_pipeline_v11"):
  110 |                 if isinstance(v11_out, dict) and str(
  142 | if __name__ == "__main__":
```

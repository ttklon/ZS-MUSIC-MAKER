# grep-таблицы `modules/mastering_ai.py`

## `import` — 5 совпадений
```
    3 | from __future__ import annotations
    4 | from pathlib import Path
    5 | from typing import Any, Dict, Optional
    6 | from app.ai.registry import registry
   26 |         from modules import mastering_pro
```

## `except` — 2 совпадений
```
   21 |         except Exception as e:
   33 |     except Exception as e:
```

## `try` — 2 совпадений
```
   14 |         try:
   25 |     try:
```

## `def` — 1 совпадений
```
    9 | def master_ai(input_wav: str, out_wav: str, reference_wav: Optional[str] = None,
```

## `return` — 3 совпадений
```
   19 |             return {"ok": True, "engine": "matchering",
   32 |         return res
   34 |         return {"ok": False, "reason": f"mastering failed: {e}"}
```

## `if` — 1 совпадений
```
   13 |     if reference_wav and registry.is_available("mastering_ai"):
```

## `with` — 1 совпадений
```
   15 |             with registry.use("mastering_ai") as m:
```

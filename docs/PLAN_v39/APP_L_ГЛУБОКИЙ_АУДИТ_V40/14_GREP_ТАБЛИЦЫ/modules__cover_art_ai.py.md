# grep-таблицы `modules/cover_art_ai.py`

## `import` — 6 совпадений
```
    3 | from __future__ import annotations
    4 | from pathlib import Path
    5 | from typing import Any, Dict
    6 | from app.ai.registry import registry
    7 | from app.ai import prompts as P
   16 |             from modules import cover_art_gen
```

## `except` — 2 совпадений
```
   21 |         except Exception as e:
   31 |         except Exception as e:
```

## `try` — 2 совпадений
```
   15 |         try:
   25 |         try:
```

## `def` — 1 совпадений
```
   10 | def render_cover_ai(title: str, artist: str, genre: str, mood: str,
```

## `return` — 4 совпадений
```
   20 |             return res
   22 |             return {"ok": False, "reason": f"no cover engine: {e}"}
   29 |             return {"ok": True, "engine": "sdxl-base-1.0", "path": out_path,
   32 |             return {"ok": False, "reason": str(e), "engine": "sdxl-base-1.0"}
```

## `if` — 1 совпадений
```
   14 |     if not registry.is_available("cover_art"):
```

## `with` — 1 совпадений
```
   23 |     with registry.use("cover_art") as m:
```

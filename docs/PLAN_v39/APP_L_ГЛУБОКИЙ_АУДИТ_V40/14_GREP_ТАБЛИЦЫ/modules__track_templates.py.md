# grep-таблицы `modules/track_templates.py`

## `import` — 5 совпадений
```
   10 | from __future__ import annotations
   12 | import json
   13 | import time
   14 | import uuid
   15 | from pathlib import Path
```

## `except` — 3 совпадений
```
   29 |         except Exception:
   60 |         except Exception:
   72 |     except Exception:
```

## `try` — 3 совпадений
```
   27 |         try:
   58 |         try:
   70 |     try:
```

## `def` — 9 совпадений
```
   25 | def _load_history() -> list[dict]:
   34 | def _save_history(items: list[dict]) -> None:
   41 | def save_template(name: str, recipe: dict) -> str:
   55 | def list_templates() -> list[dict]:
   66 | def load_template(tid: str) -> dict | None:
   76 | def delete_template(tid: str) -> bool:
   85 | def push_history(track_meta: dict) -> None:
   94 | def get_history(limit: int = 100) -> list[dict]:
   98 | def clear_history() -> None:
```

## `return` — 11 совпадений
```
   28 |             return json.loads(HIST_FILE.read_text(encoding="utf-8"))
   30 |             return []
   31 |     return []
   52 |     return tid
   63 |     return out
   69 |         return None
   71 |         return json.loads(f.read_text(encoding="utf-8"))
   73 |         return None
   80 |         return True
   81 |     return False
   95 |     return _load_history()[-limit:]
```

## `if` — 3 совпадений
```
   26 |     if HIST_FILE.exists():
   68 |     if not f.exists():
   78 |     if f.exists():
```

## `for` — 1 совпадений
```
   57 |     for f in TPL_DIR.glob("*.json"):
```

# grep-таблицы `app/ai/llm_service.py`

## `import` — 3 совпадений
```
    3 | from __future__ import annotations
    4 | import json
    5 | from typing import Any, Optional
```

## `except` — 4 совпадений
```
   20 |     except Exception:
   27 |         except Exception:
   41 |     except Exception:
   44 |         except Exception:
```

## `try` — 4 совпадений
```
   13 |     try:
   21 |         try:
   39 |     try:
   42 |         try:
```

## `def` — 2 совпадений
```
    8 | def complete(handle: Any, system: str, user: str, max_tokens: int = 1024,
   31 | def complete_json(handle: Any, system: str, user: str, max_tokens: int = 2048,
```

## `return` — 9 совпадений
```
   12 |         return ""
   19 |         return res["choices"][0]["message"]["content"].strip()
   26 |             return res["choices"][0]["text"].strip()
   28 |             return ""
   35 |         return None
   38 |         return None
   40 |         return json.loads(txt[s:e + 1])
   43 |             return json.loads(txt[s:e + 1].replace("'", '"'))
   45 |             return None
```

## `if` — 3 совпадений
```
   11 |     if handle is None:
   34 |     if not txt:
   37 |     if s < 0 or e <= s:
```

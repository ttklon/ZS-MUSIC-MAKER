# grep-таблицы `app/core/cover_gen.py`

## `import` — 6 совпадений
```
    3 | from __future__ import annotations
    5 | import random
    6 | from pathlib import Path
   11 |         from PIL import Image, ImageDraw, ImageFilter
   14 |     from app.core.security_utils import safe_hash
   36 |     from app.core.font_utils import load_pil_font
```

## `except` — 1 совпадений
```
   12 |     except Exception as e:
```

## `try` — 1 совпадений
```
   10 |     try:
```

## `def` — 1 совпадений
```
    9 | def make_cover(recipe: dict, out_png: str, size: int = 1500) -> dict:
```

## `return` — 2 совпадений
```
   13 |         return {"ok": False, "reason": f"Pillow missing: {e}"}
   45 |     return {"ok": True, "path": out_png}
```

## `for` — 1 совпадений
```
   29 |     for i in range(0, size, 28):
```

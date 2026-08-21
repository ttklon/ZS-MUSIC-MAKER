# grep-таблицы `modules/cover_art_gen.py`

## `import` — 7 совпадений
```
   12 | from __future__ import annotations
   14 | import hashlib
   15 | import random
   16 | from pathlib import Path
   17 | from typing import Any
   20 |     from PIL import Image, ImageDraw, ImageFilter, ImageFont
  172 |     from app.core.font_utils import load_pil_font
```

## `print` — 2 совпадений
```
  246 |         print(r)
  248 |         print("PIL missing")
```

## `except` — 1 совпадений
```
   23 | except Exception:
```

## `try` — 1 совпадений
```
   19 | try:
```

## `def` — 10 совпадений
```
   41 | def generate(
  121 | def _fill_gradient(img: Image.Image, c1, c2) -> None:
  133 | def _apply_glitch(img, rng):
  143 | def _apply_neon_grid(img, rng, colour):
  155 | def _apply_sun(img, rng):
  165 | def _apply_chrome(img, rng):
  170 | def _load_font(size: int):
  176 | def _center_text(
  221 | def _wrap_title(text: str, max_chars: int = 14):
  236 | def _contrast(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
```

## `return` — 9 совпадений
```
   53 |         return {"ok": False, "reason": "PIL not available"}
  118 |     return {"ok": True, "path": out_path, "style": style, "seed": seed, "size": size}
  140 |     return img
  152 |     return img
  162 |     return img
  167 |     return img
  173 |     return load_pil_font(size, bold=True)
  233 |     return out or [text[:max_chars]]
  238 |     return (20, 20, 25) if lum > 140 else (245, 245, 250)
```

## `if` — 9 совпадений
```
   52 |     if not PIL_OK:
   55 |     if seed is None:
   65 |     if style == "glitch":
  186 |     if letter_spacing > 0:
  225 |         if len(cur) + len(w) + 1 <= max_chars:
  228 |             if cur:
  231 |     if cur:
  241 | if __name__ == "__main__":
  242 |     if PIL_OK:
```

## `for` — 10 совпадений
```
   94 |     for line in lines:
  124 |     for y in range(h):
  129 |         for x in range(w):
  135 |     for _ in range(rng.randint(5, 12)):
  148 |     for x in range(0, w, step):
  150 |     for y in range(0, h, step):
  159 |     for r in range(min(w, h) // 3, 0, -6):
  190 |         for ch in text:
  197 |         for ch, cw in zip(text, widths):
  224 |     for w in words:
```

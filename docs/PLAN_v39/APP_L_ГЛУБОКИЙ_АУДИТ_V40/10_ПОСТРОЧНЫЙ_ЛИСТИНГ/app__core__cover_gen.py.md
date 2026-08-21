# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/cover_gen.py`

**Всего строк:** 45

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 26 | 57.8 |
| import | 6 | 13.3 |
| blank | 4 | 8.9 |
| try_block | 2 | 4.4 |
| return | 2 | 4.4 |
| comment | 2 | 4.4 |
| docstring | 1 | 2.2 |
| def | 1 | 2.2 |
| loop | 1 | 2.2 |

## Полный листинг с классификацией
```
    1 [docstring ] """v6 Cover — minimal-art обложка через Pillow. Никаких сетевых зависимостей."""
    2 [blank     ] 
    3 [import    ] from __future__ import annotations
    4 [blank     ] 
    5 [import    ] import random
    6 [import    ] from pathlib import Path
    7 [blank     ] 
    8 [blank     ] 
    9 [def       ] def make_cover(recipe: dict, out_png: str, size: int = 1500) -> dict:
   10 [try_block ]     try:
   11 [import    ]         from PIL import Image, ImageDraw, ImageFilter
   12 [try_block ]     except Exception as e:
   13 [return    ]         return {"ok": False, "reason": f"Pillow missing: {e}"}
   14 [import    ]     from app.core.security_utils import safe_hash
   15 [code      ]     title = recipe.get("title") or recipe.get("theme") or "ZS Track"
   16 [code      ]     h = safe_hash(title)
   17 [code      ]     seed = int(h[:8], 16)
   18 [code      ]     rnd = random.Random(seed)
   19 [code      ]     palette = [
   20 [code      ]         [(15, 15, 20), (255, 90, 40), (255, 200, 60)],
   21 [code      ]         [(20, 8, 40), (180, 60, 200), (60, 220, 255)],
   22 [code      ]         [(6, 6, 6), (255, 40, 90), (255, 255, 255)],
   23 [code      ]         [(10, 30, 20), (0, 200, 120), (250, 230, 100)],
   24 [code      ]     ]
   25 [code      ]     bg, c1, c2 = rnd.choice(palette)
   26 [code      ]     img = Image.new("RGB", (size, size), bg)
   27 [code      ]     d = ImageDraw.Draw(img)
   28 [comment   ]     # диагональные полосы
   29 [loop      ]     for i in range(0, size, 28):
   30 [code      ]         d.line([(0, i), (i, 0)], fill=c1, width=2)
   31 [code      ]     d.rectangle(
   32 [code      ]         [size // 12, size // 2 - size // 8, size - size // 12, size // 2 + size // 8],
   33 [code      ]         fill=c2,
   34 [code      ]     )
   35 [comment   ]     # v39.4 (ШАГ 002): единый font_utils вместо hardcoded-путей
   36 [import    ]     from app.core.font_utils import load_pil_font
   37 [code      ]     font = load_pil_font(size // 10, bold=True)
   38 [code      ]     txt = title[:22].upper()
   39 [code      ]     bbox = d.textbbox((0, 0), txt, font=font)
   40 [code      ]     tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
   41 [code      ]     d.text(((size - tw) // 2, (size - th) // 2), txt, fill=bg, font=font)
   42 [code      ]     img = img.filter(ImageFilter.SMOOTH)
   43 [code      ]     Path(out_png).parent.mkdir(parents=True, exist_ok=True)
   44 [code      ]     img.save(out_png, "PNG")
   45 [return    ]     return {"ok": True, "path": out_png}
```
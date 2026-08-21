# АУДИТ ФАЙЛА: `modules/cover_art_gen.py`

**LOC:** 248  |  **Размер:** 6994 байт  |  **Проблем:** 4  |  **Risk score:** 2

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 12 | `__future__.annotations` | from |
| 14 | `hashlib` | import |
| 15 | `random` | import |
| 16 | `pathlib.Path` | from |
| 17 | `typing.Any` | from |
| 20 | `PIL.Image` | from |
| 20 | `PIL.ImageDraw` | from |
| 20 | `PIL.ImageFilter` | from |
| 20 | `PIL.ImageFont` | from |
| 172 | `app.core.font_utils.load_pil_font` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 41 | `generate` | 77 | 9 | ✅ |
| 121 | `_fill_gradient` | 9 | 2 | ❌ |
| 133 | `_apply_glitch` | 7 | 1 | ❌ |
| 143 | `_apply_neon_grid` | 9 | 2 | ❌ |
| 155 | `_apply_sun` | 7 | 1 | ❌ |
| 165 | `_apply_chrome` | 2 | 0 | ❌ |
| 170 | `_load_font` | 3 | 0 | ❌ |
| 176 | `_center_text` | 42 | 3 | ❌ |
| 221 | `_wrap_title` | 12 | 5 | ❌ |
| 236 | `_contrast` | 2 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 2 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 12** — import 'annotations' не используется в теле файла

  ```
         10 | """
         11 | 
  >>>    12 | from __future__ import annotations
         13 | 
         14 | import hashlib
  ```

- **строка 20** — import 'ImageFont' не используется в теле файла

  ```
         18 | 
         19 | try:
  >>>    20 |     from PIL import Image, ImageDraw, ImageFilter, ImageFont
         21 | 
         22 |     PIL_OK = True
  ```

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 246** — print() вместо logger

  ```
        244 |             "Turkish Nights", "ZS", "output/covers/test_cover.png", style="neon"
        245 |         )
  >>>   246 |         print(r)
        247 |     else:
        248 |         print("PIL missing")
  ```

- **строка 248** — print() вместо logger

  ```
        246 |         print(r)
        247 |     else:
  >>>   248 |         print("PIL missing")
  ```

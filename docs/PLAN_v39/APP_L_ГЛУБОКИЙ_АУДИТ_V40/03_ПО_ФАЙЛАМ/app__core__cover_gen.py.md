# АУДИТ ФАЙЛА: `app/core/cover_gen.py`

**LOC:** 45  |  **Размер:** 1780 байт  |  **Проблем:** 2  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `__future__.annotations` | from |
| 5 | `random` | import |
| 6 | `pathlib.Path` | from |
| 14 | `app.core.security_utils.safe_hash` | from |
| 36 | `app.core.font_utils.load_pil_font` | from |
| 11 | `PIL.Image` | from |
| 11 | `PIL.ImageDraw` | from |
| 11 | `PIL.ImageFilter` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 9 | `make_cover` | 36 | 3 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 3** — import 'annotations' не используется в теле файла

  ```
          1 | """v6 Cover — minimal-art обложка через Pillow. Никаких сетевых зависимостей."""
          2 | 
  >>>     3 | from __future__ import annotations
          4 | 
          5 | import random
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 9** — public function 'make_cover' без docstring

  ```
          7 | 
          8 | 
  >>>     9 | def make_cover(recipe: dict, out_png: str, size: int = 1500) -> dict:
         10 |     try:
         11 |         from PIL import Image, ImageDraw, ImageFilter
  ```

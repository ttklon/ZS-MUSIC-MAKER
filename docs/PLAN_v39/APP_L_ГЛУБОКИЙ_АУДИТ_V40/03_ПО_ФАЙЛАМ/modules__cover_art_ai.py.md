# АУДИТ ФАЙЛА: `modules/cover_art_ai.py`

**LOC:** 32  |  **Размер:** 1418 байт  |  **Проблем:** 2  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `__future__.annotations` | from |
| 4 | `pathlib.Path` | from |
| 5 | `typing.Any` | from |
| 5 | `typing.Dict` | from |
| 6 | `app.ai.registry.registry` | from |
| 7 | `app.ai.prompts` | from |
| 16 | `modules.cover_art_gen` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 10 | `render_cover_ai` | 22 | 4 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 3** — import 'annotations' не используется в теле файла

  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker - modules/cover_art_ai.py (v38, SDXL Base 1.0 fp16)."""
  >>>     3 | from __future__ import annotations
          4 | from pathlib import Path
          5 | from typing import Any, Dict
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 10** — public function 'render_cover_ai' без docstring

  ```
          8 | 
          9 | 
  >>>    10 | def render_cover_ai(title: str, artist: str, genre: str, mood: str,
         11 |                     out_path: str, size: int = 1024) -> Dict[str, Any]:
         12 |     prompt = P.build_cover_prompt(title, artist, genre, mood)
  ```

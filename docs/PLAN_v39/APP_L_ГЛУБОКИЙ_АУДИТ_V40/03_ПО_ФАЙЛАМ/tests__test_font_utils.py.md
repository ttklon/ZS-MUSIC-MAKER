# АУДИТ ФАЙЛА: `tests/test_font_utils.py`

**LOC:** 29  |  **Размер:** 780 байт  |  **Проблем:** 1  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `__future__.annotations` | from |
| 5 | `app.core.font_utils` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 8 | `test_candidates_non_empty` | 5 | 0 | ❌ |
| 16 | `test_candidates_regular_variant` | 2 | 0 | ❌ |
| 21 | `test_env_override` | 3 | 0 | ❌ |
| 27 | `test_load_pil_font_returns_something` | 2 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 3** — import 'annotations' не используется в теле файла

  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker — tests for app/core/font_utils (ШАГ 002)."""
  >>>     3 | from __future__ import annotations
          4 | 
          5 | from app.core import font_utils as F
  ```

# АУДИТ ФАЙЛА: `tests/test_isrc.py`

**LOC:** 78  |  **Размер:** 2420 байт  |  **Проблем:** 1  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `__future__.annotations` | from |
| 5 | `app.core.isrc` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 8 | `test_placeholder_detection` | 4 | 0 | ❌ |
| 15 | `test_valid_isrc_positive` | 3 | 0 | ❌ |
| 21 | `test_valid_isrc_negative` | 6 | 0 | ❌ |
| 30 | `test_generate_deterministic` | 6 | 0 | ❌ |
| 39 | `test_generate_custom_country_registrant` | 5 | 0 | ❌ |
| 47 | `test_generate_from_seq_number` | 3 | 0 | ❌ |
| 53 | `test_get_isrc_fallback_empty_when_bad_input` | 6 | 0 | ❌ |
| 62 | `test_get_isrc_preserves_valid_input` | 3 | 0 | ❌ |
| 68 | `test_generate_stable_across_years_field_types` | 4 | 0 | ❌ |
| 75 | `test_get_isrc_fallback_string` | 3 | 1 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 3** — import 'annotations' не используется в теле файла

  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker — tests for app/core/isrc (ШАГ 003)."""
  >>>     3 | from __future__ import annotations
          4 | 
          5 | from app.core import isrc as I
  ```

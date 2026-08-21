# АУДИТ ФАЙЛА: `app/core/isrc.py`

**LOC:** 117  |  **Размер:** 4472 байт  |  **Проблем:** 2  |  **Risk score:** 2

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 20 | `__future__.annotations` | from |
| 22 | `hashlib` | import |
| 23 | `re` | import |
| 24 | `time` | import |
| 25 | `typing.Any` | from |
| 25 | `typing.Optional` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 30 | `is_valid_isrc` | 11 | 5 | ✅ |
| 44 | `is_placeholder_isrc` | 5 | 3 | ✅ |
| 52 | `_short_seq_from_title` | 6 | 1 | ✅ |
| 61 | `_normalize_existing` | 2 | 0 | ❌ |
| 66 | `generate_isrc` | 42 | 10 | ✅ |
| 111 | `get_isrc` | 6 | 0 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 20** — import 'annotations' не используется в теле файла

  ```
         18 | пометку UNREGISTERED (никогда не фейковый placeholder).
         19 | """
  >>>    20 | from __future__ import annotations
         21 | 
         22 | import hashlib
  ```

### MARKER_XXX — 1 шт. — 🟡 MEDIUM
**Смысл:** XXX в коде — требуется внимание
**Fix:** Закрыть отдельным шагом.

- **строка 37** — # плейсхолдеры вида XX-XXX-00-00000 отбраковываем

  ```
         35 |     if not _ISRC_RE.match(s):
         36 |         return False
  >>>    37 |     # плейсхолдеры вида XX-XXX-00-00000 отбраковываем
         38 |     core = s.replace("-", "")
         39 |     if core.startswith("XX") or (core.endswith("00000") and core[5:7] == "00"):
  ```

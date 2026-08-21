# АУДИТ ФАЙЛА: `modules/matchering_master.py`

**LOC:** 133  |  **Размер:** 4345 байт  |  **Проблем:** 2  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 17 | `__future__.annotations` | from |
| 19 | `logging` | import |
| 20 | `pathlib.Path` | from |
| 21 | `typing.Any` | from |
| 26 | `matchering` | import |
| 104 | `pydub.AudioSegment` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 33 | `match_to_reference` | 27 | 3 | ✅ |
| 63 | `master_to_stand` | 21 | 1 | ✅ |
| 87 | `master_all_stands` | 10 | 1 | ✅ |
| 100 | `_pydub_fallback` | 29 | 2 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 17** — import 'annotations' не используется в теле файла

  ```
         15 | """
         16 | 
  >>>    17 | from __future__ import annotations
         18 | 
         19 | import logging
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 133** — print() вместо logger

  ```
        131 | 
        132 | if __name__ == "__main__":
  >>>   133 |     print("Matchering available:", MG_OK)
  ```

# АУДИТ ФАЙЛА: `modules/freesound_client.py`

**LOC:** 200  |  **Размер:** 6708 байт  |  **Проблем:** 2  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 16 | `__future__.annotations` | from |
| 18 | `hashlib` | import |
| 19 | `json` | import |
| 20 | `logging` | import |
| 21 | `os` | import |
| 22 | `time` | import |
| 23 | `pathlib.Path` | from |
| 24 | `typing.Any` | from |
| 29 | `requests` | import |
| 196 | `sys` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 43 | `_load_key` | 9 | 2 | ❌ |
| 55 | `search` | 54 | 10 | ✅ |
| 112 | `_offline_search` | 30 | 5 | ✅ |
| 145 | `download_preview` | 23 | 6 | ✅ |
| 171 | `_append_manifest` | 21 | 2 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 16** — import 'annotations' не используется в теле файла

  ```
         14 | """
         15 | 
  >>>    16 | from __future__ import annotations
         17 | 
         18 | import hashlib
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 200** — print() вместо logger

  ```
        198 |     q = sys.argv[1] if len(sys.argv) > 1 else "trap 808 kick"
        199 |     res = search(q, bpm_min=120, bpm_max=160, duration_max=5.0)
  >>>   200 |     print(json.dumps(res, ensure_ascii=False, indent=2)[:2000])
  ```

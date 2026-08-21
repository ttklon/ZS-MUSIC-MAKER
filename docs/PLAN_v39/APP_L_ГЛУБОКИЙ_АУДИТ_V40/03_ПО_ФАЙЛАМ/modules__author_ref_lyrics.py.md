# АУДИТ ФАЙЛА: `modules/author_ref_lyrics.py`

**LOC:** 369  |  **Размер:** 14113 байт  |  **Проблем:** 4  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 21 | `__future__.annotations` | from |
| 23 | `hashlib` | import |
| 24 | `json` | import |
| 25 | `re` | import |
| 26 | `time` | import |
| 27 | `collections.Counter` | from |
| 28 | `pathlib.Path` | from |
| 243 | `urllib.parse` | import |
| 244 | `urllib.request` | import |
| 360 | `sys` | import |
| 147 | `whisper` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 82 | `_tokenize` | 1 | 1 | ❌ |
| 86 | `_syllables_ru` | 1 | 0 | ❌ |
| 90 | `_load_index` | 6 | 2 | ❌ |
| 99 | `_save_index` | 3 | 0 | ❌ |
| 106 | `ingest_lyrics_file` | 6 | 2 | ✅ |
| 115 | `ingest_lyrics_text` | 21 | 1 | ✅ |
| 139 | `ingest_reference_audio` | 17 | 5 | ✅ |
| 160 | `build_style_profile` | 60 | 11 | ✅ |
| 223 | `get_style_profile` | 10 | 2 | ❌ |
| 237 | `search_author_online` | 34 | 6 | ✅ |
| 274 | `fetch_and_ingest_author` | 20 | 6 | ✅ |
| 298 | `build_style_prompt` | 24 | 4 | ✅ |
| 326 | `scan_library` | 22 | 10 | ✅ |
| 351 | `list_authors` | 5 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 3 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 363** — print() вместо logger

  ```
        361 | 
        362 |     if len(sys.argv) > 1 and sys.argv[1] == "scan":
  >>>   363 |         print(json.dumps(scan_library(), ensure_ascii=False, indent=2))
        364 |     elif len(sys.argv) > 2 and sys.argv[1] == "profile":
        365 |         print(
  ```

- **строка 365** — print() вместо logger

  ```
        363 |         print(json.dumps(scan_library(), ensure_ascii=False, indent=2))
        364 |     elif len(sys.argv) > 2 and sys.argv[1] == "profile":
  >>>   365 |         print(
        366 |             json.dumps(build_style_profile(sys.argv[2]), ensure_ascii=False, indent=2)
        367 |         )
  ```

- **строка 369** — print() вместо logger

  ```
        367 |         )
        368 |     else:
  >>>   369 |         print(json.dumps(list_authors(), ensure_ascii=False, indent=2))
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 21** — import 'annotations' не используется в теле файла

  ```
         19 | """
         20 | 
  >>>    21 | from __future__ import annotations
         22 | 
         23 | import hashlib
  ```

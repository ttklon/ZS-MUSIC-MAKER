# АУДИТ ФАЙЛА: `modules/release_pack_v9.py`

**LOC:** 180  |  **Размер:** 6641 байт  |  **Проблем:** 5  |  **Risk score:** 5

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 22 | `__future__.annotations` | from |
| 24 | `json` | import |
| 25 | `shutil` | import |
| 26 | `time` | import |
| 27 | `pathlib.Path` | from |
| 161 | `sys` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 32 | `_safe_copy` | 6 | 1 | ❌ |
| 41 | `_write_json` | 4 | 0 | ❌ |
| 48 | `_readme_text` | 24 | 1 | ❌ |
| 75 | `build_release_v9` | 82 | 18 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 164** — print() вместо logger

  ```
        162 | 
        163 |     if len(sys.argv) < 2:
  >>>   164 |         print("usage: python release_pack_v9.py <release_dir>")
        165 |         sys.exit(1)
        166 |     r = build_release_v9(
  ```

- **строка 180** — print() вместо logger

  ```
        178 |         master_wav="/tmp/none.wav",
        179 |     )
  >>>   180 |     print(json.dumps(r, indent=2))
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 22** — import 'annotations' не используется в теле файла

  ```
         20 | """
         21 | 
  >>>    22 | from __future__ import annotations
         23 | 
         24 | import json
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 75** — build_release_v9: сложность ≈ 18 (>15)

  ```
         73 | 
         74 | 
  >>>    75 | def build_release_v9(
         76 |     release_dir: str,
         77 |     project_meta: dict,
  ```

### HARDCODED_POSIX_PATH — 1 шт. — 🟠 HIGH
**Смысл:** Захардкоженный POSIX-путь (/home/... /Users/...)
**Fix:** Path из config.settings/tempfile.gettempdir().

- **строка 178** — /tmp/none.wav

  ```
        176 |             "duration_s": 150,
        177 |         },
  >>>   178 |         master_wav="/tmp/none.wav",
        179 |     )
        180 |     print(json.dumps(r, indent=2))
  ```

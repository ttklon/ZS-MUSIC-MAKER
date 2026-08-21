# АУДИТ ФАЙЛА: `modules/reference_ingest.py`

**LOC:** 318  |  **Размер:** 11101 байт  |  **Проблем:** 3  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 22 | `__future__.annotations` | from |
| 24 | `hashlib` | import |
| 25 | `json` | import |
| 26 | `time` | import |
| 27 | `pathlib.Path` | from |
| 30 | `numpy` | import |
| 35 | `librosa` | import |
| 312 | `sys` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 50 | `_md5` | 5 | 2 | ❌ |
| 58 | `_cache_path` | 1 | 0 | ❌ |
| 62 | `_load_cached` | 7 | 2 | ❌ |
| 72 | `_save_cached` | 1 | 0 | ❌ |
| 77 | `_key_from_chroma` | 20 | 4 | ✅ |
| 100 | `analyze_file` | 65 | 7 | ✅ |
| 169 | `_consensus_bpm` | 16 | 4 | ✅ |
| 188 | `_consensus_key` | 10 | 2 | ✅ |
| 201 | `build_style_vector` | 77 | 12 | ✅ |
| 281 | `_guess_genre` | 14 | 8 | ❌ |
| 298 | `_guess_mood` | 9 | 7 | ❌ |
| 175 | `_norm` | 5 | 2 | ❌ |
| 232 | `_wavg` | 13 | 5 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 315** — print() вместо logger

  ```
        313 | 
        314 |     if len(sys.argv) < 2:
  >>>   315 |         print("usage: python reference_ingest.py <ref1> [ref2 ...]")
        316 |         sys.exit(1)
        317 |     r = build_style_vector(sys.argv[1:])
  ```

- **строка 318** — print() вместо logger

  ```
        316 |         sys.exit(1)
        317 |     r = build_style_vector(sys.argv[1:])
  >>>   318 |     print(json.dumps(r, ensure_ascii=False, indent=2))
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
         24 | import hashlib
  ```

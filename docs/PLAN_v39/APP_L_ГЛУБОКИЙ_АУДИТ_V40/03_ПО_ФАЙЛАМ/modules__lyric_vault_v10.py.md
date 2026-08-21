# АУДИТ ФАЙЛА: `modules/lyric_vault_v10.py`

**LOC:** 252  |  **Размер:** 8437 байт  |  **Проблем:** 3  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 15 | `__future__.annotations` | from |
| 17 | `hashlib` | import |
| 18 | `json` | import |
| 19 | `logging` | import |
| 20 | `time` | import |
| 21 | `collections.Counter` | from |
| 22 | `pathlib.Path` | from |
| 23 | `typing.Any` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 33 | `_syllable_count` | 14 | 3 | ✅ |
| 50 | `add_line` | 26 | 1 | ✅ |
| 79 | `load_all` | 27 | 9 | ✅ |
| 109 | `find_lines` | 38 | 14 | ✅ |
| 150 | `mark_used` | 8 | 1 | ✅ |
| 161 | `rebuild_index` | 18 | 0 | ❌ |
| 182 | `export_lrc` | 27 | 4 | ✅ |
| 212 | `_recently_used_ids` | 21 | 8 | ❌ |
| 236 | `_load_usage` | 6 | 2 | ❌ |
| 245 | `_save_usage` | 2 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 15** — import 'annotations' не используется в теле файла

  ```
         13 | """
         14 | 
  >>>    15 | from __future__ import annotations
         16 | 
         17 | import hashlib
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 161** — public function 'rebuild_index' без docstring

  ```
        159 | 
        160 | 
  >>>   161 | def rebuild_index() -> dict[str, Any]:
        162 |     all_lines = load_all()
        163 |     idx = {
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 252** — print() вместо logger

  ```
        250 | if __name__ == "__main__":
        251 |     r = rebuild_index()
  >>>   252 |     print(json.dumps(r, ensure_ascii=False, indent=2))
  ```

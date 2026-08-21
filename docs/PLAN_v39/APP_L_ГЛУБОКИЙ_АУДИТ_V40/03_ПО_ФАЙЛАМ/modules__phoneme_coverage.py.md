# АУДИТ ФАЙЛА: `modules/phoneme_coverage.py`

**LOC:** 137  |  **Размер:** 4950 байт  |  **Проблем:** 4  |  **Risk score:** 5

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 14 | `__future__.annotations` | from |
| 16 | `json` | import |
| 17 | `collections.Counter` | from |
| 18 | `pathlib.Path` | from |
| 19 | `typing.Any` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 45 | `_collect_transcripts` | 21 | 10 | ✅ |
| 69 | `compute_coverage` | 39 | 0 | ✅ |
| 111 | `_make_suggestions` | 21 | 10 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### SILENT_EXCEPT_PASS — 2 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 53** — except: pass — тихое подавление ошибок

  ```
         51 |         try:
         52 |             texts.append(p.read_text(encoding="utf-8"))
  >>>    53 |         except Exception:
         54 |             pass
         55 |     for p in VAULT_DIR.rglob("*.json"):
  ```

- **строка 64** — except: pass — тихое подавление ошибок

  ```
         62 |                     if isinstance(item, dict) and "transcript" in item:
         63 |                         texts.append(str(item["transcript"]))
  >>>    64 |         except Exception:
         65 |             pass
         66 |     return texts
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 14** — import 'annotations' не используется в теле файла

  ```
         12 | """
         13 | 
  >>>    14 | from __future__ import annotations
         15 | 
         16 | import json
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 137** — print() вместо logger

  ```
        135 | if __name__ == "__main__":
        136 |     r = compute_coverage()
  >>>   137 |     print(json.dumps(r, ensure_ascii=False, indent=2))
  ```

# АУДИТ ФАЙЛА: `app/core/orchestrator_v11_patch.py`

**LOC:** 401  |  **Размер:** 14524 байт  |  **Проблем:** 7  |  **Risk score:** 9

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 8 | `__future__.annotations` | from |
| 10 | `json` | import |
| 11 | `os` | import |
| 12 | `sys` | import |
| 13 | `time` | import |
| 14 | `traceback` | import |
| 15 | `pathlib.Path` | from |
| 328 | `struct` | import |
| 329 | `wave` | import |
| 378 | `tempfile` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 21 | `_safe_print` | 4 | 1 | ❌ |
| 28 | `_load_deps` | 21 | 4 | ❌ |
| 52 | `run_full_pipeline_v11` | 269 | 42 | ✅ |
| 324 | `_minimal_pipeline_fallback` | 30 | 5 | ✅ |
| 365 | `register` | 9 | 2 | ❌ |
| 377 | `_self_test` | 20 | 2 | ❌ |
| 60 | `prog` | 6 | 2 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### SILENT_EXCEPT_PASS — 2 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 339** — except: pass — тихое подавление ошибок

  ```
        337 |                 wf.setframerate(44100)
        338 |                 wf.writeframes(struct.pack("<" + "h" * 44100, *([0] * 44100)))
  >>>   339 |         except Exception:
        340 |             pass
        341 |     lp = os.path.join(release_dir, "lyrics.txt")
  ```

- **строка 65** — except: pass — тихое подавление ошибок

  ```
         63 |             try:
         64 |                 progress_cb(stage, pct, msg)
  >>>    65 |             except Exception:
         66 |                 pass
         67 | 
  ```

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 23** — print() вместо logger

  ```
         21 | def _safe_print(msg):
         22 |     try:
  >>>    23 |         print(msg)
         24 |     except UnicodeEncodeError:
         25 |         sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))
  ```

- **строка 401** — print() вместо logger

  ```
        399 | 
        400 | if __name__ == "__main__":
  >>>   401 |     print("orchestrator_v11_patch self-test:", "OK" if _self_test() else "FAIL")
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 8** — import 'annotations' не используется в теле файла

  ```
          6 | """
          7 | 
  >>>     8 | from __future__ import annotations
          9 | 
         10 | import json
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 52** — run_full_pipeline_v11: 269 LOC (>100) — декомпозиция

  ```
         50 | 
         51 | 
  >>>    52 | def run_full_pipeline_v11(
         53 |     project_id, wizard_state, expert_config=None, progress_cb=None, project_root=None
         54 | ):
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 52** — run_full_pipeline_v11: сложность ≈ 42 (>15)

  ```
         50 | 
         51 | 
  >>>    52 | def run_full_pipeline_v11(
         53 |     project_id, wizard_state, expert_config=None, progress_cb=None, project_root=None
         54 | ):
  ```

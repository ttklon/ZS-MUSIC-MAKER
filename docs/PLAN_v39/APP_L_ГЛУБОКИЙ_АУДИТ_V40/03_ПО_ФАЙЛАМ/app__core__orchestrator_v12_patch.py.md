# АУДИТ ФАЙЛА: `app/core/orchestrator_v12_patch.py`

**LOC:** 144  |  **Размер:** 4855 байт  |  **Проблем:** 2  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 17 | `__future__.annotations` | from |
| 19 | `sys` | import |
| 20 | `time` | import |
| 21 | `traceback` | import |
| 22 | `collections.abc.Callable` | from |
| 23 | `pathlib.Path` | from |
| 24 | `typing.Any` | from |
| 66 | `modules.health_v12` | from |
| 81 | `modules.master_pipeline_v12` | from |
| 122 | `modules.kpi_dashboard_v12` | from |
| 99 | `app.core.orchestrator_v11_patch` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 31 | `_safe_print` | 4 | 1 | ❌ |
| 38 | `run_full_pipeline_v12` | 96 | 10 | ✅ |
| 137 | `register` | 2 | 0 | ✅ |

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
         19 | import sys
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 33** — print() вместо logger

  ```
         31 | def _safe_print(msg: str) -> None:
         32 |     try:
  >>>    33 |         print(msg)
         34 |     except UnicodeEncodeError:
         35 |         sys.stdout.buffer.write((msg + "\n").encode("cp866", "replace"))
  ```

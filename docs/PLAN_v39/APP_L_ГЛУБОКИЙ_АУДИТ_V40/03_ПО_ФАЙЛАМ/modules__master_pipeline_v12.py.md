# АУДИТ ФАЙЛА: `modules/master_pipeline_v12.py`

**LOC:** 719  |  **Размер:** 26571 байт  |  **Проблем:** 8  |  **Risk score:** 7

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 37 | `__future__.annotations` | from |
| 39 | `json` | import |
| 40 | `sys` | import |
| 41 | `time` | import |
| 42 | `traceback` | import |
| 43 | `collections.abc.Callable` | from |
| 44 | `dataclasses.asdict` | from |
| 44 | `dataclasses.dataclass` | from |
| 44 | `dataclasses.field` | from |
| 45 | `pathlib.Path` | from |
| 46 | `typing.Any` | from |
| 71 | `sys` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 58 | `_log` | 16 | 4 | ❌ |
| 117 | `_jsonable` | 5 | 1 | ❌ |
| 130 | `_stage` | 60 | 4 | ❌ |
| 193 | `_try_import` | 5 | 1 | ❌ |
| 206 | `run_master_pipeline` | 437 | 70 | ✅ |
| 646 | `_make_human_summary` | 18 | 2 | ❌ |
| 667 | `_finalize` | 12 | 1 | ❌ |
| 682 | `run` | 14 | 0 | ✅ |
| 704 | `_demo` | 11 | 0 | ❌ |
| 94 | `as_dict` | 3 | 0 | ❌ |
| 113 | `as_dict` | 1 | 0 | ❌ |
| 225 | `progress` | 8 | 2 | ❌ |
| 256 | `_do_ri` | 8 | 4 | ❌ |
| 287 | `_do_sh` | 11 | 4 | ❌ |
| 317 | `_do_arr` | 19 | 9 | ❌ |
| 354 | `_do_mgt` | 3 | 2 | ❌ |
| 375 | `_do_lyrics` | 10 | 3 | ❌ |
| 404 | `_do_voice` | 16 | 8 | ❌ |
| 440 | `_do_master` | 3 | 2 | ❌ |
| 461 | `_do_an` | 15 | 2 | ❌ |
| 497 | `_do_release` | 27 | 4 | ❌ |
| 546 | `_do_hs` | 9 | 5 | ❌ |
| 567 | `_do_kpi` | 13 | 2 | ❌ |
| 604 | `_contains_simulation` | 15 | 6 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 83 | `StageResult` | ❌ |
| 101 | `MasterResult` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_CLASS_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 83** — public class 'StageResult' без docstring

  ```
         81 | 
         82 | @dataclass
  >>>    83 | class StageResult:
         84 |     name: str
         85 |     tz_ref: str  # секция ТЗ, к которой привязана стадия
  ```

- **строка 101** — public class 'MasterResult' без docstring

  ```
         99 | 
        100 | @dataclass
  >>>   101 | class MasterResult:
        102 |     project_id: str
        103 |     started_at: float = field(default_factory=lambda: time.time())
  ```

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 61** — print() вместо logger

  ```
         59 |     line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [master_v12] {msg}"
         60 |     try:
  >>>    61 |         print(line)
         62 |     except UnicodeEncodeError:
         63 |         sys.stdout.buffer.write((line + "\n").encode("cp866", "replace"))
  ```

- **строка 714** — print() вместо logger

  ```
        712 |     }
        713 |     r = run_master_pipeline(project_id, wizard_state=state, dry_run=True)
  >>>   714 |     print("\n" + r.human_summary)
        715 |     return 0 if r.verdict.endswith("PASS") else 1
        716 | 
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 37** — import 'annotations' не используется в теле файла

  ```
         35 | """
         36 | 
  >>>    37 | from __future__ import annotations
         38 | 
         39 | import json
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 206** — run_master_pipeline: 437 LOC (>100) — декомпозиция

  ```
        204 | 
        205 | 
  >>>   206 | def run_master_pipeline(
        207 |     project_id: str,
        208 |     wizard_state: dict[str, Any] | None = None,
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 206** — run_master_pipeline: сложность ≈ 70 (>15)

  ```
        204 | 
        205 | 
  >>>   206 | def run_master_pipeline(
        207 |     project_id: str,
        208 |     wizard_state: dict[str, Any] | None = None,
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 73** — except: pass — тихое подавление ошибок

  ```
         71 |             import sys as _s
         72 |             _s.stderr.write(f"[master_pipeline_v12] log-write failed: {e}\n")
  >>>    73 |         except Exception:
         74 |             pass
         75 | 
  ```

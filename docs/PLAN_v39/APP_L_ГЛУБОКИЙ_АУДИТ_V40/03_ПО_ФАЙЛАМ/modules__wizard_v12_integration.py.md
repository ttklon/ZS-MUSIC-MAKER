# АУДИТ ФАЙЛА: `modules/wizard_v12_integration.py`

**LOC:** 289  |  **Размер:** 11698 байт  |  **Проблем:** 9  |  **Risk score:** 7

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 21 | `__future__.annotations` | from |
| 23 | `json` | import |
| 24 | `sys` | import |
| 25 | `time` | import |
| 26 | `collections.abc.Callable` | from |
| 27 | `dataclasses.asdict` | from |
| 27 | `dataclasses.dataclass` | from |
| 27 | `dataclasses.field` | from |
| 28 | `pathlib.Path` | from |
| 29 | `typing.Any` | from |
| 133 | `modules.health_v12` | from |
| 153 | `app.core.orchestrator_v12_patch` | from |
| 202 | `modules.kpi_dashboard_v12` | from |
| 169 | `app.core.orchestrator_v11_patch` | from |
| 187 | `modules.master_pipeline_v12` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 39 | `_log` | 9 | 2 | ❌ |
| 70 | `collect_wizard_state` | 21 | 1 | ✅ |
| 94 | `bridge_wizard_to_v12` | 137 | 13 | ✅ |
| 234 | `install_into_wizard_main` | 37 | 4 | ✅ |
| 274 | `main_entry` | 11 | 0 | ✅ |
| 64 | `as_dict` | 3 | 0 | ❌ |
| 249 | `patched` | 11 | 2 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 52 | `WizardBridgeResult` | ❌ |

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 3 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 42** — print() вместо logger

  ```
         40 |     line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [wizard_v12_integ] {msg}"
         41 |     try:
  >>>    42 |         print(line)
         43 |     except UnicodeEncodeError:
         44 |         sys.stdout.buffer.write((line + "\n").encode("cp866", "replace"))
  ```

- **строка 281** — print() вместо logger

  ```
        279 |     )
        280 |     r = bridge_wizard_to_v12(proj, ui_state=state, dry_run=True)
  >>>   281 |     print(
        282 |         f"verdict={r.verdict}  stages={len(r.stages_done)}  " f"errors={len(r.errors)}"
        283 |     )
  ```

- **строка 284** — print() вместо logger

  ```
        282 |         f"verdict={r.verdict}  stages={len(r.stages_done)}  " f"errors={len(r.errors)}"
        283 |     )
  >>>   284 |     print(r.human_summary)
        285 |     return 0 if r.verdict.endswith("PASS") else 1
        286 | 
  ```

### SILENT_EXCEPT_PASS — 2 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 47** — except: pass — тихое подавление ошибок

  ```
         45 |     try:
         46 |         (LOGS / "app.log").open("a", encoding="utf-8").write(line + "\n")
  >>>    47 |     except Exception:
         48 |         pass
         49 | 
  ```

- **строка 143** — except: pass — тихое подавление ошибок

  ```
        141 |                     "health_v12", 0.05, f"стек: {hr.verdict}, {hr.percent_ready}% готов"
        142 |                 )
  >>>   143 |             except Exception:
        144 |                 pass
        145 |     except Exception as e:  # noqa: BLE001
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
         23 | import json
  ```

### MISSING_CLASS_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 52** — public class 'WizardBridgeResult' без docstring

  ```
         50 | 
         51 | @dataclass
  >>>    52 | class WizardBridgeResult:
         53 |     project_id: str
         54 |     started_at: float = field(default_factory=lambda: time.time())
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 94** — bridge_wizard_to_v12: 137 LOC (>100) — декомпозиция

  ```
         92 | 
         93 | 
  >>>    94 | def bridge_wizard_to_v12(
         95 |     project_id: str,
         96 |     ui_state: dict[str, Any] | None = None,
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 249** — public function 'patched' без docstring

  ```
        247 | 
        248 |         # замыкаем чтобы не зациклиться
  >>>   249 |         def patched(*args, **kwargs):
        250 |             project_id = kwargs.get("project_id") or (
        251 |                 args[0] if args else "wizard_project"
  ```

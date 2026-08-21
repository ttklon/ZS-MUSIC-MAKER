# АУДИТ ФАЙЛА: `app/runtime_orchestrator.py`

**LOC:** 149  |  **Размер:** 4943 байт  |  **Проблем:** 7  |  **Risk score:** 5

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 1 | `__future__.annotations` | from |
| 3 | `threading` | import |
| 4 | `time` | import |
| 5 | `uuid` | import |
| 6 | `dataclasses.dataclass` | from |
| 6 | `dataclasses.field` | from |
| 7 | `pathlib.Path` | from |
| 8 | `typing.Any` | from |
| 10 | `app.core.orchestrator.run_full_pipeline` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 30 | `__init__` | 7 | 0 | ❌ |
| 39 | `_log` | 7 | 3 | ❌ |
| 48 | `_ensure_worker` | 5 | 2 | ❌ |
| 55 | `enqueue` | 9 | 2 | ❌ |
| 66 | `enqueue_batch` | 1 | 1 | ❌ |
| 69 | `_run_loop` | 11 | 5 | ❌ |
| 82 | `_process` | 67 | 19 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 16 | `Job` | ❌ |
| 29 | `RuntimeOrchestrator` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_CLASS_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 16** — public class 'Job' без docstring

  ```
         14 | 
         15 | @dataclass
  >>>    16 | class Job:
         17 |     track_id: str
         18 |     recipe: dict[str, Any]
  ```

- **строка 29** — public class 'RuntimeOrchestrator' без docstring

  ```
         27 | 
         28 | 
  >>>    29 | class RuntimeOrchestrator:
         30 |     def __init__(self, log=None):
         31 |         self.log = log
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 1** — import 'annotations' не используется в теле файла

  ```
  >>>     1 | from __future__ import annotations
          2 | 
          3 | import threading
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 82** — _process: сложность ≈ 19 (>15)

  ```
         80 |                 self._process(job)
         81 | 
  >>>    82 |     def _process(self, job: Job):
         83 |         out_dir = Path(job.project_dir)
         84 |         out_dir.mkdir(parents=True, exist_ok=True)
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 45** — except: pass — тихое подавление ошибок

  ```
         43 |             else:
         44 |                 print(msg)
  >>>    45 |         except Exception:
         46 |             pass
         47 | 
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 44** — print() вместо logger

  ```
         42 |                 self.log.info(msg)
         43 |             else:
  >>>    44 |                 print(msg)
         45 |         except Exception:
         46 |             pass
  ```

### BLOCKING_SLEEP — 1 шт. — 🟢 LOW
**Смысл:** time.sleep() без комментария/аргументации
**Fix:** Комментарий или await asyncio.sleep().

- **строка 76** — time.sleep(...) без пояснения

  ```
         74 |                     tid = self._queue.pop(0)
         75 |             if not tid:
  >>>    76 |                 time.sleep(0.2)
         77 |                 continue
         78 |             job = self.jobs.get(tid)
  ```

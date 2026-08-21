# АУДИТ ФАЙЛА: `modules/render_queue.py`

**LOC:** 197  |  **Размер:** 6682 байт  |  **Проблем:** 5  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 11 | `__future__.annotations` | from |
| 13 | `json` | import |
| 14 | `threading` | import |
| 15 | `time` | import |
| 16 | `uuid` | import |
| 17 | `collections.abc.Callable` | from |
| 18 | `dataclasses.asdict` | from |
| 18 | `dataclasses.dataclass` | from |
| 18 | `dataclasses.field` | from |
| 19 | `pathlib.Path` | from |
| 157 | `app.core.orchestrator.Orchestrator` | from |
| 158 | `app.hw_probe.probe_hw` | from |
| 159 | `app.logger.make_logger` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 44 | `_load_state` | 6 | 2 | ❌ |
| 53 | `_save_state` | 4 | 0 | ❌ |
| 40 | `to_dict` | 1 | 0 | ❌ |
| 66 | `__init__` | 6 | 0 | ❌ |
| 75 | `_restore` | 8 | 2 | ❌ |
| 85 | `_persist` | 1 | 0 | ❌ |
| 89 | `enqueue` | 5 | 0 | ❌ |
| 96 | `enqueue_batch` | 1 | 0 | ❌ |
| 99 | `status_summary` | 5 | 1 | ❌ |
| 106 | `list_items` | 1 | 0 | ❌ |
| 109 | `cancel` | 7 | 3 | ❌ |
| 118 | `clear_done` | 2 | 0 | ❌ |
| 123 | `start` | 6 | 2 | ❌ |
| 131 | `stop` | 2 | 0 | ❌ |
| 135 | `_run_loop` | 6 | 2 | ❌ |
| 143 | `_pick_next` | 4 | 2 | ❌ |
| 150 | `_process` | 28 | 3 | ❌ |
| 181 | `morning_report` | 11 | 0 | ❌ |
| 163 | `on_stage` | 3 | 0 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 28 | `QueueItem` | ❌ |
| 60 | `RenderQueue` | ✅ |

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 11** — import 'annotations' не используется в теле файла

  ```
          9 | """
         10 | 
  >>>    11 | from __future__ import annotations
         12 | 
         13 | import json
  ```

### MISSING_CLASS_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 28** — public class 'QueueItem' без docstring

  ```
         26 | 
         27 | @dataclass
  >>>    28 | class QueueItem:
         29 |     id: str
         30 |     recipe: dict
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 181** — public function 'morning_report' без docstring

  ```
        179 | 
        180 |     # ------------------------------------------------------- morning report
  >>>   181 |     def morning_report(self) -> dict:
        182 |         done = [i for i in self.items if i.status == "done"]
        183 |         errs = [i for i in self.items if i.status == "error"]
  ```

### BLOCKING_SLEEP — 1 шт. — 🟢 LOW
**Смысл:** time.sleep() без комментария/аргументации
**Fix:** Комментарий или await asyncio.sleep().

- **строка 139** — time.sleep(...) без пояснения

  ```
        137 |             next_item = self._pick_next()
        138 |             if not next_item:
  >>>   139 |                 time.sleep(3)
        140 |                 continue
        141 |             self._process(next_item)
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 197** — print() вместо logger

  ```
        195 | if __name__ == "__main__":
        196 |     q = RenderQueue()
  >>>   197 |     print(json.dumps(q.status_summary(), indent=2))
  ```

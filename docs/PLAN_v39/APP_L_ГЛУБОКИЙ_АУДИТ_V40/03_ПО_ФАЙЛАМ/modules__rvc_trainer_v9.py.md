# АУДИТ ФАЙЛА: `modules/rvc_trainer_v9.py`

**LOC:** 234  |  **Размер:** 8324 байт  |  **Проблем:** 4  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 18 | `__future__.annotations` | from |
| 20 | `json` | import |
| 21 | `threading` | import |
| 22 | `time` | import |
| 23 | `uuid` | import |
| 24 | `collections.abc.Callable` | from |
| 25 | `pathlib.Path` | from |
| 58 | `modules.rvc_manager.detect_backend` | from |
| 193 | `modules.render_queue.enqueue` | from |
| 117 | `importlib` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 36 | `_now` | 1 | 0 | ❌ |
| 40 | `_mk_job_id` | 1 | 0 | ❌ |
| 44 | `_save_job` | 3 | 0 | ❌ |
| 50 | `_load_manifest` | 1 | 0 | ❌ |
| 55 | `probe_backend` | 22 | 1 | ✅ |
| 81 | `_build_plan` | 24 | 4 | ✅ |
| 108 | `_run_training_bg` | 38 | 8 | ✅ |
| 150 | `retrain_incremental` | 37 | 1 | ✅ |
| 190 | `schedule_night_run` | 17 | 2 | ✅ |
| 210 | `get_job` | 7 | 2 | ❌ |
| 220 | `list_jobs` | 10 | 2 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BLOCKING_SLEEP — 2 шт. — 🟢 LOW
**Смысл:** time.sleep() без комментария/аргументации
**Fix:** Комментарий или await asyncio.sleep().

- **строка 122** — time.sleep(...) без пояснения

  ```
        120 |             if hasattr(rvc_py, "train"):
        121 |                 for e in range(1, total + 1):
  >>>   122 |                     time.sleep(0.05)
        123 |                     job["progress"] = e / total
        124 |                     job["current_epoch"] = e
  ```

- **строка 136** — time.sleep(...) без пояснения

  ```
        134 |     # DRY: симулируем прогон эпох с обновлением прогресса (для CI/UI)
        135 |     for e in range(1, total + 1):
  >>>   136 |         time.sleep(0.001)
        137 |         job["progress"] = e / total
        138 |         job["current_epoch"] = e
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 18** — import 'annotations' не используется в теле файла

  ```
         16 | """
         17 | 
  >>>    18 | from __future__ import annotations
         19 | 
         20 | import json
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 234** — print() вместо logger

  ```
        232 | 
        233 | if __name__ == "__main__":
  >>>   234 |     print(json.dumps(probe_backend(), ensure_ascii=False, indent=2))
  ```

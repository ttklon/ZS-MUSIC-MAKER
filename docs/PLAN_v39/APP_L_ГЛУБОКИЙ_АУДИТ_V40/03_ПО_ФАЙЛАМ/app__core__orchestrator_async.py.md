# АУДИТ ФАЙЛА: `app/core/orchestrator_async.py`

**LOC:** 118  |  **Размер:** 4825 байт  |  **Проблем:** 5  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 9 | `asyncio` | import |
| 10 | `time` | import |
| 11 | `os` | import |
| 12 | `json` | import |
| 13 | `pathlib.Path` | from |
| 14 | `typing.Any` | from |
| 14 | `typing.List` | from |
| 14 | `typing.Optional` | from |
| 14 | `typing.Callable` | from |
| 15 | `dataclasses.dataclass` | from |
| 15 | `dataclasses.asdict` | from |
| 50 | `multiprocessing` | import |
| 60 | `modules.beat_constructor` | from |
| 60 | `modules.phonk_engine` | from |
| 60 | `modules.voice_cleaner` | from |
| 60 | `modules.mastering_pro` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 25 | `run_stage_async` | 16 | 2 | ❌ |
| 112 | `main_async` | 3 | 0 | ❌ |
| 44 | `__init__` | 7 | 0 | ❌ |
| 53 | `_run_limited` | 2 | 0 | ❌ |
| 57 | `run_pipeline` | 53 | 6 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 18 | `AsyncStage` | ❌ |
| 43 | `AsyncOrchestrator` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_CLASS_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 18** — public class 'AsyncStage' без docstring

  ```
         16 | 
         17 | @dataclass
  >>>    18 | class AsyncStage:
         19 |     name: str
         20 |     ok: bool = False
  ```

- **строка 43** — public class 'AsyncOrchestrator' без docstring

  ```
         41 |     return stage
         42 | 
  >>>    43 | class AsyncOrchestrator:
         44 |     def __init__(self, project_id: str, out_root: Path):
         45 |         self.project_id = project_id
  ```

### MISSING_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 25** — public function 'run_stage_async' без docstring

  ```
         23 |     reason: Optional[str] = None
         24 | 
  >>>    25 | async def run_stage_async(name: str, coro: Callable) -> AsyncStage:
         26 |     t0 = time.time()
         27 |     stage = AsyncStage(name=name)
  ```

- **строка 57** — public function 'run_pipeline' без docstring

  ```
         55 |             return await run_stage_async(name, coro)
         56 | 
  >>>    57 |     async def run_pipeline(self, wizard_state: dict):
         58 |         t_start = time.time()
         59 | 
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 115** — print() вместо logger

  ```
        113 |     orch = AsyncOrchestrator("async_test", Path("./output/async_test"))
        114 |     res = await orch.run_pipeline({"genre": "phonk", "bpm_override": 140})
  >>>   115 |     print(f"Async Pipeline Done in {res['duration_sec']}s")
        116 | 
        117 | if __name__ == "__main__":
  ```

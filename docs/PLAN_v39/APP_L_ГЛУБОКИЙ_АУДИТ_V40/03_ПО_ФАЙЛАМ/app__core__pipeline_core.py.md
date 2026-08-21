# АУДИТ ФАЙЛА: `app/core/pipeline_core.py`

**LOC:** 146  |  **Размер:** 6428 байт  |  **Проблем:** 6  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 9 | `time` | import |
| 10 | `logging` | import |
| 11 | `gc` | import |
| 12 | `json` | import |
| 13 | `os` | import |
| 14 | `pathlib.Path` | from |
| 15 | `typing.Dict` | from |
| 15 | `typing.Any` | from |
| 15 | `typing.List` | from |
| 15 | `typing.Callable` | from |
| 15 | `typing.Optional` | from |
| 16 | `dataclasses.dataclass` | from |
| 16 | `dataclasses.field` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 38 | `__init__` | 2 | 0 | ❌ |
| 42 | `execute` | 16 | 1 | ❌ |
| 61 | `__init__` | 19 | 0 | ✅ |
| 82 | `add_stage` | 2 | 0 | ❌ |
| 86 | `_save_checkpoint` | 11 | 2 | ✅ |
| 103 | `run` | 43 | 10 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 23 | `StageResult` | ❌ |
| 31 | `PipelineContext` | ❌ |
| 37 | `PipelineStage` | ❌ |
| 60 | `ZSPipeline` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_CLASS_DOCSTRING — 4 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 23** — public class 'StageResult' без docstring

  ```
         21 | 
         22 | @dataclass
  >>>    23 | class StageResult:
         24 |     name: str
         25 |     ok: bool
  ```

- **строка 31** — public class 'PipelineContext' без docstring

  ```
         29 | 
         30 | @dataclass
  >>>    31 | class PipelineContext:
         32 |     project_id: str
         33 |     config: Dict[str, Any]
  ```

- **строка 37** — public class 'PipelineStage' без docstring

  ```
         35 |     shared_data: Dict[str, Any] = field(default_factory=dict)
         36 | 
  >>>    37 | class PipelineStage:
         38 |     def __init__(self, name: str, func: Callable[[PipelineContext], Any]):
         39 |         self.name = name
  ```

- **строка 60** — public class 'ZSPipeline' без docstring

  ```
         58 |             return res
         59 | 
  >>>    60 | class ZSPipeline:
         61 |     def __init__(
         62 |         self,
  ```

### MISSING_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 42** — public function 'execute' без docstring

  ```
         40 |         self.func = func
         41 | 
  >>>    42 |     def execute(self, context: PipelineContext) -> StageResult:
         43 |         start_time = time.time()
         44 |         logger.info(f"stage={self.name} event=start")
  ```

- **строка 103** — public function 'run' без docstring

  ```
        101 |     CHECKPOINT_TTL_SEC = 24 * 3600
        102 | 
  >>>   103 |     def run(self, use_checkpoints: bool = True) -> Dict[str, Any]:
        104 |         logger.info(f"Launching pipeline for project: {self.context.project_id}")
        105 | 
  ```

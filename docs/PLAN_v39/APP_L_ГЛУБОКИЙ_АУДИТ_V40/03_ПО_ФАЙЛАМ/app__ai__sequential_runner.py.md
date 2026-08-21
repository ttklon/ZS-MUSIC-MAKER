# АУДИТ ФАЙЛА: `app/ai/sequential_runner.py`

**LOC:** 134  |  **Размер:** 5528 байт  |  **Проблем:** 6  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 4 | `__future__.annotations` | from |
| 5 | `gc` | import |
| 5 | `time` | import |
| 5 | `logging` | import |
| 6 | `dataclasses.dataclass` | from |
| 6 | `dataclasses.field` | from |
| 7 | `typing.Any` | from |
| 7 | `typing.Callable` | from |
| 7 | `typing.Dict` | from |
| 7 | `typing.List` | from |
| 7 | `typing.Optional` | from |
| 8 | `app.ai.registry.registry` | from |
| 8 | `app.ai.registry.MODEL_REGISTRY` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 124 | `_summarize` | 10 | 4 | ❌ |
| 43 | `to_dict` | 5 | 0 | ❌ |
| 52 | `__init__` | 2 | 0 | ❌ |
| 56 | `add` | 2 | 0 | ❌ |
| 60 | `sink` | 1 | 0 | ❌ |
| 63 | `run` | 58 | 10 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 17 | `AIStage` | ❌ |
| 27 | `StageReport` | ❌ |
| 39 | `RunReport` | ❌ |
| 51 | `SequentialAIRunner` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_CLASS_DOCSTRING — 4 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 17** — public class 'AIStage' без docstring

  ```
         15 | 
         16 | @dataclass
  >>>    17 | class AIStage:
         18 |     name: str
         19 |     model: Optional[str]
  ```

- **строка 27** — public class 'StageReport' без docstring

  ```
         25 | 
         26 | @dataclass
  >>>    27 | class StageReport:
         28 |     name: str
         29 |     ok: bool
  ```

- **строка 39** — public class 'RunReport' без docstring

  ```
         37 | 
         38 | @dataclass
  >>>    39 | class RunReport:
         40 |     stages: List[StageReport] = field(default_factory=list)
         41 |     total_sec: float = 0.0
  ```

- **строка 51** — public class 'SequentialAIRunner' без docstring

  ```
         49 | 
         50 | 
  >>>    51 | class SequentialAIRunner:
         52 |     def __init__(self):
         53 |         self.stages: List[AIStage] = []
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 4** — import 'annotations' не используется в теле файла

  ```
          2 | """ZS Music Maker - app/ai/sequential_runner.py (v38)
          3 | Последовательный раннер: одна тяжёлая модель в VRAM за раз."""
  >>>     4 | from __future__ import annotations
          5 | import gc, time, logging
          6 | from dataclasses import dataclass, field
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 63** — public function 'run' без docstring

  ```
         61 |         return self._sink
         62 | 
  >>>    63 |     def run(self, context: Optional[Dict[str, Any]] = None) -> RunReport:
         64 |         context = context or {}
         65 |         context["sink"] = self._sink
  ```

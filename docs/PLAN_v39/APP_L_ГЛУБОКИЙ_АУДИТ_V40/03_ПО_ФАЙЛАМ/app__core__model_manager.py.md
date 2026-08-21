# АУДИТ ФАЙЛА: `app/core/model_manager.py`

**LOC:** 62  |  **Размер:** 3064 байт  |  **Проблем:** 1  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 9 | `pathlib.Path` | from |
| 10 | `app.core.security_utils.download_file` | from |
| 11 | `app.core.logger.app_logger` | from |
| 50 | `torch` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 19 | `__init__` | 10 | 0 | ❌ |
| 31 | `ensure_model` | 14 | 3 | ✅ |
| 47 | `load_torch_model` | 12 | 1 | ✅ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 18 | `ModelManager` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_CLASS_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 18** — public class 'ModelManager' без docstring

  ```
         16 | # torch нужен ТОЛЬКО для load_torch_model → ленивый импорт внутри метода.
         17 | 
  >>>    18 | class ModelManager:
         19 |     def __init__(self):
         20 |         self.base_dir = Path(__file__).resolve().parents[2] / "models"
  ```

# АУДИТ ФАЙЛА: `modules/genre_engine.py`

**LOC:** 127  |  **Размер:** 5156 байт  |  **Проблем:** 7  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 9 | `json` | import |
| 10 | `os` | import |
| 11 | `typing.Dict` | from |
| 11 | `typing.List` | from |
| 12 | `dataclasses.dataclass` | from |
| 12 | `dataclasses.field` | from |
| 101 | `random` | import |
| 81 | `app.core.logger.app_logger` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 27 | `__new__` | 4 | 1 | ❌ |
| 33 | `__init__` | 5 | 1 | ❌ |
| 40 | `_load_defaults` | 42 | 7 | ❌ |
| 84 | `register` | 1 | 0 | ❌ |
| 87 | `get_profile` | 3 | 0 | ❌ |
| 92 | `list_genres` | 1 | 0 | ❌ |
| 96 | `__init__` | 1 | 0 | ❌ |
| 99 | `create_wizard_state` | 20 | 1 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 15 | `GenreProfile` | ❌ |
| 24 | `StyleRegistry` | ❌ |
| 95 | `GenreFactory` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_CLASS_DOCSTRING — 3 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 15** — public class 'GenreProfile' без docstring

  ```
         13 | 
         14 | @dataclass
  >>>    15 | class GenreProfile:
         16 |     name: str
         17 |     bpm_range: tuple = (120, 140)
  ```

- **строка 24** — public class 'StyleRegistry' без docstring

  ```
         22 |     tags: List[str] = field(default_factory=list)
         23 | 
  >>>    24 | class StyleRegistry:
         25 |     _instance = None
         26 | 
  ```

- **строка 95** — public class 'GenreFactory' без docstring

  ```
         93 |         return list(self.genres.keys())
         94 | 
  >>>    95 | class GenreFactory:
         96 |     def __init__(self, registry: StyleRegistry):
         97 |         self.registry = registry
  ```

### BARE_PRINT — 3 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 124** — print() вместо logger

  ```
        122 |     reg = StyleRegistry()
        123 |     factory = GenreFactory(reg)
  >>>   124 |     print(f"Available genres: {len(reg.list_genres())}")
        125 |     # Тест на конкретный жанр из 100+
        126 |     print(f"Generated Lo-Fi state: {factory.create_wizard_state('lo-fi_hip_hop')}")
  ```

- **строка 126** — print() вместо logger

  ```
        124 |     print(f"Available genres: {len(reg.list_genres())}")
        125 |     # Тест на конкретный жанр из 100+
  >>>   126 |     print(f"Generated Lo-Fi state: {factory.create_wizard_state('lo-fi_hip_hop')}")
        127 |     print(f"Generated Techno state: {factory.create_wizard_state('techno')}")
  ```

- **строка 127** — print() вместо logger

  ```
        125 |     # Тест на конкретный жанр из 100+
        126 |     print(f"Generated Lo-Fi state: {factory.create_wizard_state('lo-fi_hip_hop')}")
  >>>   127 |     print(f"Generated Techno state: {factory.create_wizard_state('techno')}")
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 99** — public function 'create_wizard_state' без docstring

  ```
         97 |         self.registry = registry
         98 | 
  >>>    99 |     def create_wizard_state(self, genre_name: str, override: dict = None) -> dict:
        100 |         profile = self.registry.get_profile(genre_name)
        101 |         import random
  ```

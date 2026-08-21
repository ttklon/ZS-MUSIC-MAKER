# АУДИТ ФАЙЛА: `config/settings.py`

**LOC:** 158  |  **Размер:** 5641 байт  |  **Проблем:** 4  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 15 | `__future__.annotations` | from |
| 17 | `os` | import |
| 18 | `dataclasses.dataclass` | from |
| 19 | `pathlib.Path` | from |
| 20 | `typing.Optional` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 25 | `_parse_dotenv` | 17 | 6 | ✅ |
| 45 | `_as_bool` | 3 | 1 | ❌ |
| 51 | `_as_int` | 6 | 2 | ❌ |
| 60 | `_as_float` | 6 | 2 | ❌ |
| 148 | `get_settings` | 4 | 1 | ❌ |
| 155 | `reset_settings` | 3 | 0 | ✅ |
| 90 | `load` | 30 | 8 | ✅ |
| 122 | `dump` | 19 | 0 | ✅ |
| 95 | `get` | 1 | 0 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 70 | `Settings` | ✅ |

## Проблемы (детально, с цитатой кода)

### GLOBAL_STATEMENT — 2 шт. — 🟡 MEDIUM
**Смысл:** global — обычно антипаттерн
**Fix:** Инкапсулировать в класс или get_*().

- **строка 149** — global — антипаттерн

  ```
        147 | 
        148 | def get_settings() -> Settings:
  >>>   149 |     global _settings
        150 |     if _settings is None:
        151 |         _settings = Settings.load()
  ```

- **строка 157** — global — антипаттерн

  ```
        155 | def reset_settings() -> None:
        156 |     """Сбрасывает кэш настроек (используется тестами)."""
  >>>   157 |     global _settings
        158 |     _settings = None
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 15** — import 'annotations' не используется в теле файла

  ```
         13 | (комментарии # и кавычки поддерживаются). .env.example остаётся шаблоном.
         14 | """
  >>>    15 | from __future__ import annotations
         16 | 
         17 | import os
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 41** — print() вместо logger

  ```
         39 |             out[k] = v.strip().strip('"').strip("'")
         40 |     except OSError as e:  # noqa: BLE001
  >>>    41 |         print(f"[settings] cannot read {path}: {e}")
         42 |     return out
         43 | 
  ```

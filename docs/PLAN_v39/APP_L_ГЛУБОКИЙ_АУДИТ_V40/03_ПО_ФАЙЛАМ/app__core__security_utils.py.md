# АУДИТ ФАЙЛА: `app/core/security_utils.py`

**LOC:** 52  |  **Размер:** 1877 байт  |  **Проблем:** 1  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 9 | `hashlib` | import |
| 10 | `requests` | import |
| 11 | `os` | import |
| 12 | `typing.Optional` | from |
| 13 | `urllib.parse.urlparse` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 15 | `safe_hash` | 2 | 0 | ✅ |
| 19 | `download_file` | 20 | 4 | ✅ |
| 41 | `get_json` | 11 | 2 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 38** — print() вместо logger

  ```
         36 |         return True
         37 |     except Exception as e:
  >>>    38 |         print(f"Download failed: {e}")
         39 |         return False
         40 | 
  ```

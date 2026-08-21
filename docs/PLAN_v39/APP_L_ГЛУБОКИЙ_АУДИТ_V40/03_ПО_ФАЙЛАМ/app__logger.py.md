# АУДИТ ФАЙЛА: `app/logger.py`

**LOC:** 43  |  **Размер:** 1166 байт  |  **Проблем:** 2  |  **Risk score:** 2

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `logging` | import |
| 4 | `os` | import |
| 5 | `sys` | import |
| 6 | `logging.handlers.RotatingFileHandler` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 28 | `setup_logger` | 15 | 1 | ❌ |
| 12 | `__init__` | 1 | 0 | ❌ |
| 15 | `write` | 4 | 1 | ❌ |
| 21 | `flush` | 4 | 1 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 9 | `SafeStream` | ✅ |

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 28** — public function 'setup_logger' без docstring

  ```
         26 | 
         27 | 
  >>>    28 | def setup_logger(name: str = "mmzs") -> logging.Logger:
         29 |     os.makedirs("logs", exist_ok=True)
         30 |     log = logging.getLogger(name)
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 24** — except: pass — тихое подавление ошибок

  ```
         22 |         try:
         23 |             self.s.flush()
  >>>    24 |         except Exception:
         25 |             pass
         26 | 
  ```

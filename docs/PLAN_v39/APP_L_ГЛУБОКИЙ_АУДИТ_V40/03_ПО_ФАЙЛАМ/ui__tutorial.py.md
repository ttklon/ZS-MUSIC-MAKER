# АУДИТ ФАЙЛА: `ui/tutorial.py`

**LOC:** 293  |  **Размер:** 14693 байт  |  **Проблем:** 3  |  **Risk score:** 2

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 8 | `json` | import |
| 9 | `os` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 14 | `_resolve_settings_file` | 13 | 5 | ❌ |
| 224 | `get_tutorial_settings` | 6 | 2 | ❌ |
| 233 | `save_tutorial_settings` | 6 | 0 | ❌ |
| 242 | `get_step` | 3 | 1 | ❌ |
| 248 | `next_step` | 14 | 1 | ❌ |
| 265 | `prev_step` | 7 | 1 | ❌ |
| 275 | `skip_tutorial` | 4 | 0 | ❌ |
| 282 | `reset_tutorial` | 2 | 0 | ❌ |
| 287 | `get_total_steps` | 1 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 248** — public function 'next_step' без docstring

  ```
        246 | 
        247 | 
  >>>   248 | def next_step() -> dict:
        249 |     settings = get_tutorial_settings()
        250 |     idx = settings.get("current_step", 0)
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 25** — except: pass — тихое подавление ошибок

  ```
         23 |             with open(new, "w", encoding="utf-8") as f:
         24 |                 f.write(payload)
  >>>    25 |     except Exception:
         26 |         pass
         27 |     return new
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 293** — print() вместо logger

  ```
        291 | if __name__ == "__main__":
        292 |     for i, s in enumerate(STEPS):
  >>>   293 |         print(f"{i+1}. {s['title']}")
  ```

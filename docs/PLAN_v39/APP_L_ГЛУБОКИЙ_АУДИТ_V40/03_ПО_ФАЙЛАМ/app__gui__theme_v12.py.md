# АУДИТ ФАЙЛА: `app/gui/theme_v12.py`

**LOC:** 261  |  **Размер:** 8494 байт  |  **Проблем:** 4  |  **Risk score:** 5

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 20 | `__future__.annotations` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 55 | `qss` | 189 | 0 | ✅ |
| 247 | `apply` | 5 | 1 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 20** — import 'annotations' не используется в теле файла

  ```
         18 | """
         19 | 
  >>>    20 | from __future__ import annotations
         21 | 
         22 | # Токены дизайн-системы v12 (RGB, без градиентов).
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 55** — qss: 189 LOC (>100) — декомпозиция

  ```
         53 | 
         54 | 
  >>>    55 | def qss() -> str:
         56 |     """Возвращает QSS для PySide6/PyQt6. Без градиентов, без картинок."""
         57 |     t = TOKENS
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 251** — except: pass — тихое подавление ошибок

  ```
        249 |     try:
        250 |         app.setStyleSheet(qss())
  >>>   251 |     except Exception:
        252 |         pass
        253 | 
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 258** — print() вместо logger

  ```
        256 | if __name__ == "__main__":
        257 |     s = qss()
  >>>   258 |     print(
        259 |         f"theme_v12 QSS length = {len(s)} chars, "
        260 |         f"tokens = {len(TOKENS)}, fonts = {len(FONTS)}"
  ```

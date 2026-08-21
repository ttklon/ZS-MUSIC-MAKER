# АУДИТ ФАЙЛА: `app/gui/theme.py`

**LOC:** 41  |  **Размер:** 1796 байт  |  **Проблем:** 1  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 6 | `PySide6.QtGui.QColor` | from |
| 6 | `PySide6.QtGui.QPalette` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 4 | `apply_dark` | 37 | 1 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 4** — public function 'apply_dark' без docstring

  ```
          2 | 
          3 | 
  >>>     4 | def apply_dark(app):
          5 |     try:
          6 |         from PySide6.QtGui import QColor, QPalette
  ```

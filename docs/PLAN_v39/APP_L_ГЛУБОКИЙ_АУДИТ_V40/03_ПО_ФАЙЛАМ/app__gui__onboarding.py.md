# АУДИТ ФАЙЛА: `app/gui/onboarding.py`

**LOC:** 236  |  **Размер:** 10876 байт  |  **Проблем:** 6  |  **Risk score:** 16

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 9 | `__future__.annotations` | from |
| 11 | `PySide6.QtWidgets.QCheckBox` | from |
| 11 | `PySide6.QtWidgets.QDialog` | from |
| 11 | `PySide6.QtWidgets.QHBoxLayout` | from |
| 11 | `PySide6.QtWidgets.QLabel` | from |
| 11 | `PySide6.QtWidgets.QPushButton` | from |
| 11 | `PySide6.QtWidgets.QTextBrowser` | from |
| 11 | `PySide6.QtWidgets.QVBoxLayout` | from |
| 230 | `sys` | import |
| 232 | `PySide6.QtWidgets.QApplication` | from |
| 212 | `modules.user_profile.is_first_run` | from |
| 212 | `modules.user_profile.mark_onboarded` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 207 | `maybe_show_onboarding` | 14 | 4 | ✅ |
| 224 | `show_help_tour` | 2 | 0 | ✅ |
| 139 | `__init__` | 39 | 1 | ❌ |
| 180 | `render` | 12 | 0 | ❌ |
| 194 | `prev` | 3 | 1 | ❌ |
| 199 | `next` | 5 | 1 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 138 | `OnboardingDialog` | ❌ |

## Проблемы (детально, с цитатой кода)

### SECURITY_EVAL — 3 шт. — 🔴 CRITICAL
**Смысл:** eval()/exec() — вектор RCE
**Fix:** Убрать. ast.literal_eval или явный парсер.

- **строка 218** — exec() — потенциально опасно

  ```
        216 |         return False
        217 |     d = OnboardingDialog(parent)
  >>>   218 |     d.exec()
        219 |     if d.dont_show.isChecked() or True:  # всегда фиксируем, что первый запуск прошёл
        220 |         mark_onboarded()
  ```

- **строка 226** — exec() — потенциально опасно

  ```
        224 | def show_help_tour(parent=None) -> None:
        225 |     """Ручной вызов тура из меню «Помощь»."""
  >>>   226 |     OnboardingDialog(parent).exec()
        227 | 
        228 | 
  ```

- **строка 236** — exec() — потенциально опасно

  ```
        234 |     a = QApplication(sys.argv)
        235 |     d = OnboardingDialog()
  >>>   236 |     d.exec()
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 9** — import 'annotations' не используется в теле файла

  ```
          7 | """
          8 | 
  >>>     9 | from __future__ import annotations
         10 | 
         11 | from PySide6.QtWidgets import (
  ```

### MISSING_CLASS_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 138** — public class 'OnboardingDialog' без docstring

  ```
        136 | 
        137 | 
  >>>   138 | class OnboardingDialog(QDialog):
        139 |     def __init__(self, parent=None):
        140 |         super().__init__(parent)
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 180** — public function 'render' без docstring

  ```
        178 |         self.render()
        179 | 
  >>>   180 |     def render(self):
        181 |         s = TOUR_STEPS[self.step]
        182 |         self.title.setText(s["title"])
  ```

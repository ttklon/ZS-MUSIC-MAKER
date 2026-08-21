# grep-таблицы `app/gui/onboarding.py`

## `import` — 5 совпадений
```
    9 | from __future__ import annotations
   11 | from PySide6.QtWidgets import (
  212 |         from modules.user_profile import is_first_run, mark_onboarded
  230 |     import sys
  232 |     from PySide6.QtWidgets import QApplication
```

## `except` — 1 совпадений
```
  213 |     except Exception:
```

## `try` — 1 совпадений
```
  211 |     try:
```

## `def` — 6 совпадений
```
  139 |     def __init__(self, parent=None):
  180 |     def render(self):
  194 |     def prev(self):
  199 |     def next(self):
  207 | def maybe_show_onboarding(parent=None) -> bool:
  224 | def show_help_tour(parent=None) -> None:
```

## `class` — 1 совпадений
```
  138 | class OnboardingDialog(QDialog):
```

## `return` — 3 совпадений
```
  214 |         return False
  216 |         return False
  221 |     return True
```

## `if` — 5 совпадений
```
  195 |         if self.step > 0:
  200 |         if self.step < len(TOUR_STEPS) - 1:
  215 |     if not is_first_run():
  219 |     if d.dont_show.isChecked() or True:  # всегда фиксируем, что первый запуск прошёл
  229 | if __name__ == "__main__":
```

## `for` — 1 совпадений
```
  166 |         for b in (self.btn_prev, self.btn_skip):
```

## `exec` — 3 совпадений
```
  218 |     d.exec()
  226 |     OnboardingDialog(parent).exec()
  236 |     d.exec()
```

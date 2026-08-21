# SECURITY_EVAL — eval()/exec() — вектор RCE

**Severity:** 🔴 CRITICAL
**Всего:** 4
**Как чинить:** Убрать. ast.literal_eval или явный парсер.

## Все вхождения

### `app/gui/onboarding.py` — 3 шт.
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

### `main.py` — 1 шт.
- **строка 182** — exec() — потенциально опасно
  ```
        180 |         w.setWindowTitle(f"ZS Music Maker v{VERSION} — Desktop Wizard")
        181 |         w.show()
  >>>   182 |         rc = app.exec()
        183 |         raise SystemExit(rc)
        184 |     except SystemExit:
  ```

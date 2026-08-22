# APP_L v40 — triage ШАГОВ 0001–0004: SECURITY_EVAL

The four critical findings in `05_ПЛАН_ИСПРАВЛЕНИЙ.md` were inspected against the current source. They are `QDialog.exec()` / `QApplication.exec()` attribute calls that enter the Qt event loop, not Python builtin `exec()` or `eval()` calls and therefore not dynamic source execution.

The source of the false positive was `tools/deep_audit_v40.py`: it classified every method named `.exec()` as RCE. The detector now reports `SECURITY_EVAL` only for an AST `Name` call to the builtins `eval` or `exec`. It still flags direct `eval('...')` and `exec('...')`, while correctly excluding `dialog.exec()` and `application.exec()`.

| Planned items | Classification | Action |
|---|---|---|
| 0001–0003: `app/gui/onboarding.py` | False positive; Qt dialog event loop | No application code change |
| 0004: `main.py` | False positive; Qt application event loop | No application code change |
| Audit detector | Confirmed defect | Corrected and regression-tested |

Acceptance: focused detector tests — **2 passed**. Full `pytest tests/ -q` — **239 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

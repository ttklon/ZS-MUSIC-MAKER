# APP_L v40 — GUI theme application observability

The GUI theme helper previously swallowed `setStyleSheet()` failures. The application could continue starting, but callers had no indication whether the requested QSS theme was actually applied.

`theme_v12.apply()` now preserves nonblocking behavior and returns additive status. Successful application returns `applied`; a setter exception returns typed `failed` information. The function does not claim Qt availability or successful visual rendering when the setter fails.

Focused regressions use a small fake application to verify successful QSS delivery and explicit failure reporting without requiring PySide or a display server.

Acceptance: focused theme suite — **2 passed**. Full `pytest tests/ -q` — **314 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **88 SILENT_EXCEPT_PASS** (from 89), none in `app/gui/theme_v12.py`, and **879 total heuristic records** across **249** Python files. Raw audit JSON remains intentionally ignored.

# APP_L v40 — SILENT_EXCEPT_PASS: GUI theme startup diagnostic

A confirmed silent exception in `main._try_launch_gui_pyside()` previously discarded failures from `theme_v12.apply(app)`. The failure remains non-fatal so the Wizard can start with default visual styling, but it now reports a safe diagnostic through `_safe_print` with the exception reason.

A focused regression replaces GUI dependencies with minimal fakes, makes the theme apply function raise `RuntimeError("theme boom")`, and verifies that the event-loop exit remains normal while the exact fallback diagnostic is emitted. This fixes one observable startup fallback rather than mechanically changing the many other exception handlers, which require context-specific policy review.

Acceptance: focused GUI diagnostic test — **1 passed**. Full `pytest tests/ -q` — **245 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

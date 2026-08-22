# APP_L v40 — semantic DEAD_IMPORT cleanup

The deep audit now follows the established AST audit semantics for three non-runtime import classes: `__future__` compiler directives, relative package re-exports and lines deliberately annotated `# noqa`. This eliminates report noise without suppressing ordinary imports that are actually unused.

After reviewing every remaining candidate, three genuine unused imports were removed: `ImageFont` in `modules/cover_art_gen.py`, `Path` in `tests/test_render_queue.py`, and `os`/`Path` in `tests/test_settings.py`. Optional `torch_directml` probes remain intentionally guarded by `# noqa`; package `__init__` exports remain deliberate API bindings.

A raw audit regeneration records **923 findings across 209 files**, down from 934 immediately after the first v40 detector correction. The remaining categories are not represented as resolved and require individual semantic work.

Acceptance: targeted semantic/audit/settings/queue tests — **13 passed**. Full `pytest tests/ -q` — **244 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

# APP_L v40 — KPI Dashboard persistence observability

KPI Dashboard may persist JSON and Markdown reports after computing a verdict. Previously, report-write errors were silently suppressed, so the returned dashboard could not distinguish intentionally unsaved reports from an attempted write that failed.

`Dashboard` now includes additive `persistence` state. When both report writes complete, it records `saved` with the attempted paths; a directory or write failure records typed `failed` data. The checklist, percentage, verdict and rendered report content retain their prior behavior. A failed write is never represented as a saved artifact.

Focused regressions write reports to a temporary root and simulate a Markdown `disk full` error, verifying both success evidence and the failed-return state. No production report publication is claimed.

Acceptance: focused KPI Dashboard persistence suite — **2 passed**. Full `pytest tests/ -q` — **319 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **85 SILENT_EXCEPT_PASS** (from 86), none in `modules/kpi_dashboard_v12.py`, and **878 total heuristic records** across **252** Python files. Raw audit JSON remains intentionally ignored.

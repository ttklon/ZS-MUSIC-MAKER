# APP_L v40 — KPI AI-detector observability

KPI readiness accepts AI-detector reports from heterogeneous sources. Previously, an unparseable scalar value was silently skipped; a later nested score could still be used, but the report did not retain evidence that malformed data had been ignored.

`check_ai_detector_with_diagnostics()` now returns the normalized score together with typed malformed-value diagnostics. The established `check_ai_detector()` scalar API remains a compatibility wrapper. Malformed values do not manufacture an AI score; nested valid values are still normalized according to the prior percentage contract.

Focused regressions cover a malformed top-level value followed by a valid nested percentage and a report with no recoverable score. No detector inference or AI-content determination is claimed.

Acceptance: focused KPI detector suite — **2 passed**. Full `pytest tests/ -q` — **316 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **87 SILENT_EXCEPT_PASS** (from 88), none in `modules/hit_kpi_monitor_v11.py`, and **878 total heuristic records** across **250** Python files. Raw audit JSON remains intentionally ignored.

# APP_L v40 — KPI readiness decomposition

`kpi_dashboard_v12._tz_percent()` combined repository file checks, health-report overrides, checklist construction, percentage calculation and advice generation. This made the distinction between a file being present and its related internal module actually importing difficult to verify.

The implementation now separates filesystem evidence (`_filesystem_tz_checks()`), health-constrained downgrades (`_apply_health_constraints()`) and checklist summary construction (`_checklist_summary()`). `_tz_percent()` retains its compatibility parameters, deliberately ignores the historically unused pipeline/smoke arguments, and orchestrates the same evidence sequence.

The focused regression provides deterministic filesystem evidence and a health report where `modules.rvc_manager` and `app.core.musicgen_texture` fail while the KPI module remains available. It proves only RVC and MusicGen readiness are downgraded, the remaining two checklist entries stay confirmed, percentage remains 50%, and exactly two actionable advice lines are produced. It does not claim real RVC or MusicGen runtime availability.

Acceptance: focused KPI readiness suite — **1 passed**. Full `pytest tests/ -q` — **275 passed**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **29 HIGH_COMPLEXITY** (from 30), no high-complexity record in `modules/kpi_dashboard_v12.py`, **27 LONG_FUNCTION** (from 28), and **881 total heuristic records** across **225** Python files. Raw audit JSON remains intentionally ignored.

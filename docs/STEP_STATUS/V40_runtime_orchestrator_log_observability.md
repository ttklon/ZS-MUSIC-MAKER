# APP_L v40 — RuntimeOrchestrator diagnostic observability

`RuntimeOrchestrator._log()` printed when no external sink was supplied and silently swallowed every exception raised by an optional sink. A failed injected diagnostic sink therefore made the attempted runtime message disappear with no evidence of the failure.

The method now uses the module logger for its normal fallback, has an explicit `None` return type and docstring, and reports an injected-sink failure through a warning. The worker/job control flow is unchanged: diagnostics remain non-fatal, but the failed diagnostic route is visible to the operator or test harness.

The regression supplies a sink whose `info()` raises `RuntimeError`, calls `_log()`, asserts the warning, and stops the worker in a `finally` block. The adjacent result-summary regression remains green, proving the earlier extracted result contract continues to work.

Acceptance: focused RuntimeOrchestrator diagnostics suite — **2 passed**. Full `pytest tests/ -q` — **258 passed**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit records **325 BARE_PRINT** (from 326), **119 SILENT_EXCEPT_PASS** (from 120), no selected record in `app/runtime_orchestrator.py`, and **905 total heuristic records** across **217** Python files. Raw audit JSON is intentionally ignored.

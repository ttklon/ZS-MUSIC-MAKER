# APP_L v40 — health-report collection decomposition

`health_v12.collect()` mixed external/internal probing, weighted readiness scoring, verdict selection, advice construction and report persistence. The audit classified it as high complexity, making the capability-report contract difficult to validate without exercising all local optional dependencies.

The workflow is now separated into `_collect_external_checks()`, `_collect_internal_checks()`, `_calculate_readiness()`, `_append_advice()` and `_write_report()`. `collect()` remains the public orchestration entry point. The scoring weights, GUI alternative requirement, RED/YELLOW/GREEN thresholds, advice text and persisted JSON shape are preserved.

The deterministic regression replaces the probe registry and hardware probe with stubs. It verifies external/internal aggregation, the established 62-point weighted score, YELLOW verdict, internal missing-module advice and JSON persistence. It neither downloads nor loads optional models; current environment capabilities remain reported by the real probe when the application runs normally.

Acceptance: focused health-collection test — **1 passed**. Full `pytest tests/ -q` — **269 passed**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **33 HIGH_COMPLEXITY** records (from 34), no high-complexity record in `modules/health_v12.py`, and **886 total heuristic records** across **222** Python files. The raw audit JSON remains intentionally ignored.

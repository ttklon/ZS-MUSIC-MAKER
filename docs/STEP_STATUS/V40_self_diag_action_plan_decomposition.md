# APP_L v40 — self-diagnostic action-plan decomposition

`self_diag_v13.collect_action_plan()` combined filesystem severity handling, health guidance, KPI guidance, smoke guidance, advice truncation and the all-clear fallback in one high-complexity function. The resulting user-facing diagnostic policy was difficult to review in isolation.

The action planner now delegates these independent sections to `_append_layout_actions()`, `_append_health_actions()`, `_append_kpi_actions()` and `_append_smoke_actions()`. The public function preserves order and wording policy: red/yellow layout items first, then health, KPI, smoke and the all-clear fallback only when no report state yields a line. Existing five-item health and three-item KPI advice caps are preserved.

Focused regressions verify combined red/yellow layout, YELLOW health advice truncation, RED KPI advice truncation, failed smoke wording, and the all-clear result for unknown/empty report snapshots. No external health, KPI, smoke or model service is run.

Acceptance: focused self-diagnostic suite — **2 passed**. Full `pytest tests/ -q` — **274 passed**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **31 HIGH_COMPLEXITY** (from 32), no high-complexity record in `modules/self_diag_v13.py`, and **884 total heuristic records** across **224** Python files. Raw audit JSON remains intentionally ignored.

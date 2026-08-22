# APP_L v40 — BLOCKING_SLEEP semantic scope

After the interruptible worker, karaoke and onboarding changes, the remaining `BLOCKING_SLEEP` records were not shipped runtime waits: two module-local `_self_test()` delays, test fixtures, and the audit’s own detector/report source. Counting them as production responsiveness defects obscured the now-empty operational category.

`deep_audit_v40.py` now computes AST line ranges for functions named `_self_test*`. Its blocking-sleep rule still reports every unannotated production `time.sleep()`, but excludes test files, the audit support files already excluded from path auditing, and only the computed `_self_test` ranges. Inline-comment handling remains unchanged: documented production sleeps are still exempt under the existing rule.

The focused semantic test contains an unannotated production sleep and a module-local self-test sleep, then adds a pytest fixture and audit-report source. It requires the production sleep to remain flagged while all three non-production cases remain absent. This is classification correction, not a claim that arbitrary `sleep` calls are safe.

Acceptance: focused deep-audit regression suite — **8 passed**. Full `pytest tests/ -q` — **260 passed**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **0 BLOCKING_SLEEP**, **35 HIGH_COMPLEXITY**, **29 LONG_FUNCTION**, **119 SILENT_EXCEPT_PASS**, **325 BARE_PRINT**, and **898 total heuristic records** across **218** Python files. The generated raw JSON remains intentionally ignored.

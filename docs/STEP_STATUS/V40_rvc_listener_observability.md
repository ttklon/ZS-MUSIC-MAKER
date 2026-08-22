# APP_L v40 — RVC listener observability

`RVCTrainer` isolates progress listeners so one UI callback cannot prevent training lifecycle updates from reaching other listeners. Previously, a failing callback was silently suppressed, leaving no operator evidence that a progress consumer had stopped receiving updates.

The trainer now accumulates typed `listener_errors` while continuing delivery to later listeners. This does not alter training status, model discovery or backend execution; it only exposes a failed observer and preserves nonblocking delivery to healthy observers. No RVC training, backend invocation or model output is claimed by the test.

Focused regression registers one failing listener and one healthy listener, proving the healthy listener receives the actual `TrainingJob` while the callback failure is recorded.

Acceptance: focused RVC listener suite — **1 passed**. Full `pytest tests/ -q` — **308 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **93 SILENT_EXCEPT_PASS** (from 94). The selected listener record is removed; separate RVC backend-probe, dataset-copy and progress-parser records remain open. The audit reports **882 total heuristic records** across **244** Python files. Raw audit JSON remains intentionally ignored.

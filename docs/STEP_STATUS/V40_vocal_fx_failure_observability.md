# APP_L v40 — vocal-FX failure observability

`process_vocal()` previously treated two filesystem failure paths as silent: an unsuccessful copy after a non-critical delay-throw failure could leave no usable output without an explicit result, and inability to remove a temporary FX file disappeared after a successful render.

The delay-throw fallback now returns a failure result with the write error if it cannot copy the last valid stage to the requested output. The clean-only finalization path likewise includes the filesystem reason. Temporary file removal remains non-fatal, but the success response now exposes `cleanup_warnings` with typed filename diagnostics. This preserves the DSP pipeline’s existing behavior and does not claim any unavailable neural vocal processing.

Focused regressions use fake DSP result objects only. They verify a `disk full` fallback-copy failure returns `ok=False` with an explicit reason, while a simulated locked temporary double file returns `ok=True` with an inspectable cleanup warning.

Acceptance: focused vocal-FX suite — **2 passed**. Full `pytest tests/ -q` — **282 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **110 SILENT_EXCEPT_PASS** (from 112), none in `modules/vocal_fx.py`, and **877 total heuristic records** across **230** Python files. Raw audit JSON remains intentionally ignored.

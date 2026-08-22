# APP_L v40 — RuntimeOrchestrator result decomposition

`RuntimeOrchestrator._process()` mixed worker lifecycle state transitions, the full-pipeline call, stage-output traversal, warning/action filtering, desktop result shaping and error finalization. The audit classified it as high complexity, making its output contract harder to review independently from its thread/job lifecycle.

The stage interpretation and desktop response shaping now live in the pure `_summarize_pipeline_result()` helper. `_process()` remains responsible for directory setup, job state/progress, calling the pipeline, failure handling and completion time. The existing result keys are preserved: `pipeline`, `master`, `master_path`, `release.release_dir`, and `ai_detector` with sanitized flags/advice.

The focused regression supplies mastering, polish, release-pack and hit-score stages. It verifies polish precedence over the mastering fallback, release location, hit-score fields, and whitespace/type filtering for warnings and advice. It does not execute the full generation pipeline.

Acceptance: focused result-summary test — **1 passed**. Full `pytest tests/ -q` — **257 passed**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **35 HIGH_COMPLEXITY** records (from 36), no high-complexity record in `app/runtime_orchestrator.py`, and **907 total heuristic records** across **217** Python files. The generated raw JSON is intentionally ignored.

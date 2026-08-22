# APP_L v40 — RVC training honesty

The former non-dry RVC path imported `rvc_python`, then advanced artificial epochs with `time.sleep()` without invoking a verified backend API. It ended as `done_unverified`, which could still be read as a completed training attempt despite no model invocation or `.pth` output.

A non-dry request now terminates as **`blocked_backend`**. Its persisted log states whether a callable `train` symbol was detected or the import failed, and explicitly states that no backend invocation or model output was claimed. This is a capability block, not an inference or training result. The pre-existing dry path is retained for CI/UI progress only; its code comment now identifies its short pacing as simulation rather than backend work.

The focused suite verifies both contracts. The existing dry test still requires `done_dry` and the explicit no-model log. The added non-dry test runs synchronously in the sandbox and requires `blocked_backend` plus the persisted no-invocation/no-output statement.

Acceptance: focused RVC trainer suite — **2 passed**. Full `pytest tests/ -q` — **255 passed**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit: **8 BLOCKING_SLEEP** records (from 10 before this package), **36 HIGH_COMPLEXITY**, **29 LONG_FUNCTION**, and **908 total heuristic records** across **215** Python files. No `BLOCKING_SLEEP` record remains for `modules/rvc_trainer_v9.py`; raw JSON remains intentionally ignored.

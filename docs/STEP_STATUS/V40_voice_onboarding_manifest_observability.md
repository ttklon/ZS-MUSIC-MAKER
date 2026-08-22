# APP_L v40 — voice-onboarding manifest observability

`_load_manifest()` previously used `except Exception: pass` when an existing onboarding manifest could not be parsed. The compatible fallback empty plan was useful, but a malformed or unreadable persisted file became invisible and could later be overwritten without an operator-visible reason.

The recovery path now catches only `OSError` and `json.JSONDecodeError`, emits a module warning containing the failure reason, and returns the same empty-plan shape as before: `steps`, `started_at`, and `completed_at`. Missing manifests remain a normal, quiet first-run condition.

The regression writes malformed JSON, redirects the module manifest path to its temporary file, and verifies both the unchanged fallback object and the warning. It does not create or modify the repository voice vault.

Acceptance: focused manifest recovery test — **1 passed**. Full `pytest tests/ -q` — **256 passed**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit shows **120 SILENT_EXCEPT_PASS** records (from 121), no such record in `modules/voice_onboarding.py`, and **907 total heuristic records** across **216** Python files. The generated raw audit JSON remains ignored.

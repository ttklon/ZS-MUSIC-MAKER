# APP_L v40 — local Ollama observability

Legacy lyrics generation optionally calls a local Ollama HTTP endpoint. Previously, a service outage, malformed response or non-200 response collapsed into `None` without distinguishing local-service unavailability from an empty response.

`_try_ollama_with_diagnostics()` now returns additive local-service provenance. It distinguishes `responded`, `empty_response`, `http_error` and typed `unavailable` failure. The established `_try_ollama()` helper remains a text-or-`None` compatibility wrapper, so unavailable Ollama does not imply successful lyric generation.

Focused regressions simulate an unavailable local service and a nonempty HTTP response. No remote endpoint, local model, lyric text generation or inference is claimed.

Acceptance: focused local Ollama suite — **2 passed**. Full `pytest tests/ -q` — **321 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **84 SILENT_EXCEPT_PASS** (from 85), none in `modules/lyrics_gen.py`, and **879 total heuristic records** across **253** Python files. Raw audit JSON remains intentionally ignored.

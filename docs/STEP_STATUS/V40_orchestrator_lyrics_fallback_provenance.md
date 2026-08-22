# APP_L v40 — orchestrator lyrics-router fallback provenance

The pipeline can safely emit local-template lyrics when an LLM router cannot provide usable text. That fallback is intentional, but a router exception or an empty/failed router response was previously discarded; the returned template result did not distinguish no router from a failed router attempt.

`_stage_lyrics()` now preserves additive `fallback_attempts` provenance when `LLMRouter` raises, returns a non-dictionary result, or returns no usable lyrics text. The established local-template fallback remains successful, marked `fallback_used=True`, with the same `provider` and `reason` fields. A successful usable LLM response retains its prior result contract.

Focused regressions simulate a connection failure and an empty nominally successful router response. They use test doubles only; no local or remote LLM service was contacted, no model was loaded, and no generated lyrics are claimed.

Acceptance: focused suite — **2 passed**. Full `pytest tests/ -q` — **328 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**; `git diff --check` successful. Fresh deep audit reports **79 SILENT_EXCEPT_PASS** (from 80) and **881 total heuristic records** across **256** Python files. `MISSING_DOCSTRING` is **321** and `MISSING_CLASS_DOCSTRING` is **115** because two new test classes are intentionally concise test doubles; raw audit JSON remains ignored and was not committed.

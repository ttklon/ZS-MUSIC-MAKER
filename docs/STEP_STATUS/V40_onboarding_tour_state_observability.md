# APP_L v40 — onboarding tour-state observability

A malformed persisted onboarding-tour state previously fell back to the safe initial-tour state without an operational record. UI startup remained available, but corruption or filesystem decoding failure was invisible to diagnostics.

`load_state()` now logs the typed read/JSON failure and retains the existing safe default: `{"tour_done": false, "last_step": 0}`. The change does not claim a restored user state; it only makes the fallback visible while preserving nonblocking onboarding startup.

Focused regression supplies malformed JSON and verifies both the safe default and warning. No GUI interaction or state recovery is claimed.

Acceptance: focused onboarding-state suite — **1 passed**. Full `pytest tests/ -q` — **307 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **94 SILENT_EXCEPT_PASS** (from 95), none in `modules/onboarding_tour.py`, and **882 total heuristic records** across **243** Python files. The raw audit JSON remains intentionally ignored.

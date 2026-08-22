# APP_L v40 — legacy lyrics author-style observability

The deprecated `lyrics_gen_v8` orchestrator can optionally obtain an author-reference style profile. A failure in profile lookup or ingestion was previously swallowed, so generated lyrics exposed only `author_style_used: false`; callers could not distinguish an unrequested reference from a missing profile or an operational failure.

The author-reference path now has a diagnostic helper that returns explicit `not_requested`, `profile_unavailable`, `available`, or `failed` state. `generate_lyrics_v8()` returns this additive state in `author_style` while retaining the existing prompt/boolean helper and `author_style_used` field. The compatibility wrapper preserves the established monkeypatchable orchestration seam. Its diagnostic handoff is context-local, avoiding cross-request global state and related audit findings.

Focused regressions simulate a failed reference store and verify the typed fallback diagnostic while retaining the two-value helper contract. They also verify generation returns additive author-style provenance. The established orchestration regression passes unchanged. No remote author ingestion, local model generation or reference-style content is claimed.

Acceptance: focused observability and existing orchestration suites — **3 passed, 1 expected deprecation warning**. Full `pytest tests/ -q` — **301 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **99 SILENT_EXCEPT_PASS** (from 100), none in `modules/lyrics_gen_v8.py`, no `GLOBAL_STATEMENT` category, and **882 total heuristic records** across **240** Python files. The raw audit JSON remains intentionally ignored.

# APP_L v40 — phoneme coverage recovery observability

Voice Vault phoneme coverage previously ignored unreadable text transcripts and malformed JSON manifests through two silent exception handlers. Valid transcripts continued to be counted, but a user could not distinguish an empty coverage result from skipped corrupt input.

The scanner now provides `_collect_transcripts_with_errors()`, retaining valid text while collecting typed filename diagnostics for unreadable UTF-8/I/O text and malformed JSON. The historical private list-only helper remains available. `compute_coverage()` persists `transcript_read_errors` alongside the coverage report, so recovery is non-fatal and inspectable.

The focused regression uses an isolated temporary vault containing one valid text transcript and one malformed JSON file. It verifies valid transcript count, one JSON decode diagnostic and persistence of the diagnostic field. It does not access the repository Voice Vault or any model backend.

Acceptance: focused phoneme-coverage suite — **1 passed**. Full `pytest tests/ -q` — **280 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **112 SILENT_EXCEPT_PASS** (from 114), none in `modules/phoneme_coverage.py`, and **877 total heuristic records** across **229** Python files. Raw audit JSON remains intentionally ignored.

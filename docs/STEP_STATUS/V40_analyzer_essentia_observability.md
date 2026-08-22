# APP_L v40 — Analyzer Essentia observability

Single-track analysis provides core librosa-based metrics and optionally enriches the result with Essentia danceability. Previously, a failed Essentia import or descriptor operation was silently ignored, producing an empty `essentia` map indistinguishable from a completed optional analysis with no descriptors.

The result now includes additive `essentia_status`. Successful descriptor extraction is marked `applied`; an unavailable or failed optional backend retains the core analysis and explicit typed failure data. The existing `essentia` value remains an empty object on fallback, and no danceability result is fabricated.

Focused regression mocks the core audio features, blocks Essentia import and verifies core result construction plus explicit optional-backend failure. No real media analysis or Essentia inference is claimed.

Acceptance: focused Analyzer Essentia suite — **1 passed**. Full `pytest tests/ -q` — **317 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **86 SILENT_EXCEPT_PASS** (from 87), none in `modules/analyzer.py`, and **878 total heuristic records** across **251** Python files. Raw audit JSON remains intentionally ignored.

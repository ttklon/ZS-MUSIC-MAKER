# APP_L v40 — TrendScout hot-topics observability

The remaining `get_hot_topics()` DuckDuckGo enrichment fallback previously swallowed online-search errors. The resulting built-in topic list did not state whether online topics had been retrieved, whether the function had used cache, or whether the live source had failed.

`get_hot_topics_with_diagnostics()` now returns topics with provenance. Cached responses are marked `cache`; built-in topics are marked `built_in`; an actual online enrichment is marked `live_plus_built_in`. A failed DuckDuckGo lookup retains the built-in topics but records the typed error. The legacy `get_hot_topics()` list API remains a wrapper, so callers retain their previous return type.

Focused regression simulates an offline search and verifies explicit diagnostics, retained built-in topics and compatibility list output. No network lookup or live-topic claim was made.

Acceptance: focused TrendScout suite — **3 passed**. Full `pytest tests/ -q` — **306 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **95 SILENT_EXCEPT_PASS** (from 96), none in `agents/trend_scout.py`, and **883 total heuristic records** across **242** Python files. The raw audit JSON remains intentionally ignored.

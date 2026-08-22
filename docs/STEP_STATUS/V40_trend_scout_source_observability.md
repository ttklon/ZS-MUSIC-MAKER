# APP_L v40 — TrendScout source observability

`scout_trends()` previously collapsed failed DuckDuckGo retrieval and failed local slang loading into the same list-only result. A caller could not distinguish cached trends, live/local contributions or built-in fallback phrases, and a failed source could appear indistinguishable from a successful empty response.

The new `scout_trends_with_diagnostics()` returns trends together with source provenance and typed failed-source diagnostics. The established `scout_trends()` function remains a compatible list-returning wrapper. Fresh cached data is marked `cache`; an exhausted source path is marked `built_in_fallback` and does not claim live trend retrieval. No network call, real-time source content or local slang capability was executed by the tests.

Focused regressions verify cached provenance and simulate failed DuckDuckGo plus failed local slang loading, preserving a deterministic built-in fallback and the compatibility list API.

Acceptance: focused TrendScout suite — **2 passed**. Full `pytest tests/ -q` — **305 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **96 SILENT_EXCEPT_PASS** (from 98). The two `scout_trends()` source paths are resolved; one separate `get_hot_topics()` online fallback remains at `agents/trend_scout.py:155` and is not claimed resolved. The audit reports **883 total heuristic records** across **242** Python files. Raw audit JSON remains intentionally ignored.

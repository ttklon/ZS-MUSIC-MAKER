# APP_L v40 — sample-acquisition license-filter observability

`agents.sample_hunter.hunt()` optionally filters online sample search results through the commercial-use license manager. Previously, any validator failure was swallowed and unvalidated online results proceeded as if filtering had completed. Because license provenance is safety-critical, that behavior could expose sources without a completed commercial-use assessment.

The filter now returns additive `license_filter` state. When validation succeeds it is marked `applied`. If the validator cannot be imported or raises, online results are withheld entirely and the response reports `failed_closed` with a typed error; local samples remain available. If filtering is not requested, the state is explicitly `not_requested`. Existing `samples`, `online`, `local` and `provenance` fields remain available.

Focused regressions inject an approving validator to confirm real filtering and inject a runtime validator failure to prove unverified online sources are withheld while local sources survive. No external search, download, licensing determination or sample-use clearance is claimed.

Acceptance: focused sample-license suite — **2 passed**. Full `pytest tests/ -q` — **303 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **98 SILENT_EXCEPT_PASS** (from 99), none in `agents/sample_hunter.py`, and **883 total heuristic records** across **241** Python files. The raw audit JSON remains intentionally ignored.

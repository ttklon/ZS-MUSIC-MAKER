# APP_L v40 — triage ШАГОВ 0009–0119: DEAD_IMPORT baseline

The first broad medium-priority finding class required validation before any bulk deletion. The deep audit treated `from __future__ import annotations` as an ordinary unused runtime import, producing a large set of false positives. Such imports are Python compiler directives and cannot be evaluated by a textual “referenced twice” heuristic.

`tools/deep_audit_v40.py` now omits `__future__` imports from its runtime dead-import candidate set. The regression proves that `from __future__ import annotations` does not create `DEAD_IMPORT`, while an actual `import unused_module` still produces the expected issue.

This is a classification correction for the generated remediation list, not a claim that every remaining DEAD_IMPORT entry is resolved. Re-export imports and remaining ordinary imports require separate semantic review before any deletion.

Acceptance: focused audit tests — **3 passed**. Full `pytest tests/ -q` — **243 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

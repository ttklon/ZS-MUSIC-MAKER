# APP_L v40 — production POSIX path findings reduced to zero

The final remaining `HARDCODED_POSIX_PATH` record came from `tools/deep_audit_v40_expand.py`, where the audit report generator contains a literal pattern describing `/home`, `/Users` and `/tmp`. It is metadata for audit output, not a runtime filesystem target. The audit meta-tool set is therefore excluded from this specific source-path finding category, alongside test fixtures already excluded in the preceding scoped change.

The detector remains active for all ordinary production and operational source files. A fresh audit now reports **0 `HARDCODED_POSIX_PATH` findings** and **916 total findings across 210 files**. This resolves the high-priority path category without deleting necessary privacy fixtures or disabling real production path detection.

Acceptance: focused path-audit tests — **6 passed**. Full `pytest tests/ -q` — **247 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

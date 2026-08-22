# APP_L v40 — hardcoded path audit scope

The deep audit previously reported test redaction fixtures such as `/home/alice/...`, test cache-key fixtures and its own `/home|/tmp` detection expression as HIGH production portability defects. Those strings are intentionally required to validate PII/path filtering or describe the detector itself.

`HARDCODED_POSIX_PATH` is now emitted only for production-source files. Tests remain covered by their own behavior assertions, and production literal paths remain detected. The updated raw audit reports **1 remaining production POSIX-path finding** and **917 total findings across 210 files**; it does not claim the remaining finding is resolved.

Acceptance: focused path-audit tests — **5 passed**. Full `pytest tests/ -q` — **246 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

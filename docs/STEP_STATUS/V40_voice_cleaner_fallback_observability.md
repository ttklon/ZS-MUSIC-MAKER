# APP_L v40 — legacy voice-cleaner fallback observability

The compatibility `clean_vocal()` wrapper intentionally preserves the failed DSP-chain result while attempting a raw-file copy for legacy callers. Previously, the copy attempt was silently suppressed, so callers could not tell whether a compatible output existed after the cleaner failed.

The wrapper now adds `fallback_copy` diagnostics to the unchanged failed-chain response. A successful copy reports its output path; a failed copy reports the typed error and augments the reason. The actual cleaning DSP, noisereduce fallback and public success contract are unchanged.

Focused regressions replace the cleaner with a failed-chain result. They prove that successful raw-copy recovery is reported and writes the output, while a simulated `disk full` copy failure remains `ok=False` with explicit diagnostics. No real audio processing, model inference or optional package claim is made.

Acceptance: focused legacy voice-cleaner suite — **2 passed**. Full `pytest tests/ -q` — **285 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **108 SILENT_EXCEPT_PASS** (from 109), none in `modules/voice_cleaner.py`, and **877 total heuristic records** across **232** Python files. Raw audit JSON remains intentionally ignored.

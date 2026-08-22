# APP_L v40 — mastering LUFS observability

The canonical mastering module uses `pyloudnorm` only when it is available. A runtime failure inside that optional meter was previously hidden and silently replaced with a dBFS-derived estimate. The master itself could be valid, but callers could not determine whether `final_lufs` was measured by the ITU-oriented optional meter or estimated.

`_measure_lufs()` now returns both the numeric result and structured provenance. Successful optional measurement reports `lufs_engine: pyloudnorm`. Missing support reports the existing dBFS estimate as `unavailable`; a runtime meter failure logs a warning and reports `lufs_engine: dbfs_estimate`, `lufs_status: failed` and the typed error. `_try_numpy_dsp()` exposes this state alongside the existing master metrics. The compatibility `_loudness_lufs()` function still returns only the numeric value.

Focused regressions simulate a meter that rejects its input and prove the explicit fallback status, typed error and warning. They also prove the normal NumPy DSP path remains finite and labels its absence of the optional dependency as an estimate rather than a true LUFS reading. No actual optional metering backend, model or external mastering engine is claimed.

Acceptance: focused mastering LUFS suite — **2 passed**. Full `pytest tests/ -q` — **289 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **106 SILENT_EXCEPT_PASS** (from 107), none in `modules/mastering.py`, and **878 total heuristic records** across **234** Python files. The raw audit JSON remains intentionally ignored.

# APP_L v40 — Chanson master-bus observability

The Chanson Engine’s optional Pedalboard master bus previously swallowed every processing failure and returned a track report that did not disclose whether the final mix had received the requested high-pass, compression and limiter chain. A raw NumPy mix can still be a valid output, but it is not evidence of successful Pedalboard mastering.

The master bus is now isolated in `_apply_master_bus()`. The result report includes `master_bus`: successful optional processing is marked `pedalboard`; missing support is `numpy_raw_mix / unavailable`; a processing failure returns the unmodified raw mix plus `numpy_raw_mix / failed`, a typed error and an operational warning. The final WAV path and core synthesis behavior remain unchanged.

Focused regressions verify both unavailable and injected-failure paths preserve the exact raw stereo mix and disclose fallback state. No Pedalboard effect, mastered audio artifact or external audio backend was executed in these tests.

Acceptance: focused Chanson master-bus suite — **2 passed**. Full `pytest tests/ -q` — **297 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **101 SILENT_EXCEPT_PASS** (from 102), and the selected former master-bus finding is removed. One separate `SILENT_EXCEPT_PASS` remains in `modules/chanson_engine.py` at line 99 for optional guitar effects; it is not claimed resolved by this batch. The audit reports **880 total heuristic records** across **238** Python files. Raw audit JSON remains intentionally ignored.

# APP_L v40 — hit-score LUFS observability

The hit scorer exposes a `loudness_lufs` metric, but its optional `pyloudnorm` analysis previously swallowed runtime failures and returned an RMS-based pseudo-LUFS value without provenance. That made a fallback estimate indistinguishable from a completed optional measurement.

The scoring implementation now isolates the existing RMS pseudo-LUFS calculation and adds `_loudness_lufs_status()`. A successful optional read reports `engine: pyloudnorm`; missing support is marked `rms_estimate / unavailable`; an analysis failure logs a warning and reports `rms_estimate / failed` with a typed error. `score_track()` includes this provenance beneath `metrics.loudness_lufs` while preserving the established `score` and `raw` fields and the compatibility two-value helper.

Focused regressions simulate an optional meter rejecting a short clip and verify the explicit estimate provenance, typed error, warning and unchanged score/raw tuple compatibility. They also verify the missing-backend label. No optional measurement, media analysis or chart-performance capability is falsely claimed.

Acceptance: focused hit-score LUFS suite — **2 passed**. Full `pytest tests/ -q` — **291 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **105 SILENT_EXCEPT_PASS** (from 106), none in `modules/hit_scorer.py`, and **878 total heuristic records** across **235** Python files. The raw audit JSON remains intentionally ignored.

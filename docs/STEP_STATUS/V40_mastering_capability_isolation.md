# APP_L v40 — mastering optional capability isolation

`process_mastering()` previously changed module-level `HAS_PEDALBOARD` and `HAS_PYLOUDNORM` flags after a single runtime failure. Those flags describe import availability, so mutating them meant one malformed file or transient backend fault could permanently force all subsequent tracks onto the fallback implementation.

The mastering call now initializes `pedalboard_available` and `loudnorm_available` as per-run copies of imported capability flags. A failure changes only the current call’s fallback branch. `normalize_master_loudness()` likewise uses a local loudness availability value.

The regression injects a failing `AudioFile` while the pedalboard capability flag is true, confirms the current master completes through `numpy_rms_safe`, validates the output file, and proves that the global pedalboard capability remains true for a later run.

Acceptance: focused mastering isolation test — **1 passed**. Full `pytest tests/ -q` — **251 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

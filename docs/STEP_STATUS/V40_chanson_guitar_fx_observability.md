# APP_L v40 — Chanson guitar-effects observability

The Chanson guitar synthesizer optionally applies Pedalboard chorus and reverb. Its failure path previously returned the dry waveform with no indication that the requested effects chain had not run. The overall synthesis report could therefore not distinguish dry NumPy guitar synthesis from successfully processed guitar effects.

The optional chain is now isolated in `_apply_guitar_effects()`. Its status is retained for the current render and reported under `guitar_fx` by `synthesize_chanson_track()`. Unavailable Pedalboard support is labelled `numpy_guitar / unavailable`; a runtime failure logs a warning and reports `numpy_guitar / failed` with a typed error, retaining the exact dry waveform. The existing `generate_guitar_chord()` waveform return remains compatible.

Focused regressions verify both unavailable and injected-failure paths retain the original dry signal and return explicit status. They do not execute Pedalboard effects or claim a processed audio artifact.

Acceptance: focused Chanson guitar-effects suite — **2 passed**. Full `pytest tests/ -q` — **299 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **100 SILENT_EXCEPT_PASS** (from 101), none in `modules/chanson_engine.py`, and **881 total heuristic records** across **239** Python files. The raw audit JSON remains intentionally ignored.

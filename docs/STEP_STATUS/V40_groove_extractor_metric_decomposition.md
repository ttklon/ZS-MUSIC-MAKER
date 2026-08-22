# APP_L v40 — groove-extractor metric decomposition

`extract_groove()` combined librosa spectral extraction, frame-to-step aggregation, swing calculation, triplet detection, kick-pattern change detection and drop-intensity calculation in one high-complexity path. The refactor separates these concerns into helper functions while retaining the public extractor output fields and short-track result.

`_frequency_envelopes()` retains the low/snare/high-band spectral masks. `_step_envelopes()` retains the 16th-note aggregation and 8-bar bound. `_swing_value()`, `_has_triplet_rolls()`, `_pattern_changes()` and `_drop_intensity()` preserve the existing rhythmic formulas. The public extractor still raises clearly when librosa is unavailable; this sandbox run does not claim reference-audio inference.

Focused tests exercise pure helper behavior only: frame grouping, nonzero swing, dense three-step kick detection, time-marked pattern change and positive drop intensity. No audio file is read and no model/runtime backend is invoked.

Acceptance: focused groove metric suite — **2 passed**. Full `pytest tests/ -q` — **277 passed**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **28 HIGH_COMPLEXITY** (from 29), no high-complexity record in `modules/groove_extractor.py`, **26 LONG_FUNCTION** (from 27), and **880 total heuristic records** across **226** Python files. Raw audit JSON remains intentionally ignored.

# APP_L v40 — CyberSynth master-bus observability

CyberSynth optionally applies a Pedalboard high-pass, compressor and limiter to its deterministic local-DSP mix. A processing failure previously returned a WAV result without disclosing whether that effects chain had executed.

The master bus is now isolated in `_apply_master_bus()`, and `synthesize_track()` returns additive `master_bus` provenance. Missing effects support is `numpy_raw_mix / unavailable`; a failed effects chain retains the raw mix with a typed failed status. This does not represent raw synthesis as Pedalboard-processed audio.

Focused regression verifies unavailable Pedalboard support preserves the exact mix and reports explicit fallback state without rendering audio. No external effect backend or audio output was claimed.

Acceptance: focused CyberSynth effects suite — **1 passed**. Full `pytest tests/ -q` — **311 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **90 SILENT_EXCEPT_PASS** (from 91). The selected master-bus record is removed; a separate optional lead-effects fallback remains at `modules/cyber_synth.py:86`. The audit reports **881 total heuristic records** across **247** Python files. Raw audit JSON remains intentionally ignored.

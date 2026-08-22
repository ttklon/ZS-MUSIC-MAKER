# PLAN_v39 — ШАГ 090: DSP spectral acceptance and golden artifacts

The versioned audio fixture set now contains deterministic local-DSP baselines for a **15-second stereo beat**, a **10-second mono vocal surrogate**, and a **10-second stereo master**. `tools/generate_audio_goldens.py` exposes `golden_vocal_signal()` so the vocal fixture is generated from inspectable synthesis code rather than an opaque binary.

`tests/test_pro_audio_dsp.py` checks the committed vocal duration, channel count, peak, RMS and spectral centroid, then rerenders the deterministic signal and enforces RMS/centroid drift within 5%. Existing beat and master suites continue to enforce the same feature-level regression bounds. The 10-second vocal reference measures 44.1 kHz, one channel, peak approximately 0.1655, RMS approximately 0.0620 and centroid approximately 842 Hz.

Acceptance: targeted beat/vocal/master golden tests — 14 passed. Full `pytest tests/ -q` — **213 passed**; `compileall` successfully; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**. This covers available deterministic local DSP; optional Matchering runtime remains blocked and is not represented as a real golden inference result.

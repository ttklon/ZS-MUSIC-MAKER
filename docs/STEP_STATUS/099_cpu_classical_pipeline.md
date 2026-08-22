# PLAN_v39 — ШАГ 099: CPU-классический pipeline regression

The public classical `run_full_pipeline()` result now exposes `master_path`, the actual streaming master produced by successful mastering. Callers can consume the final artifact without parsing internal stage structures; the regression cross-checks this value against the mastering stage output.

The new regression temporarily blocks `torch` import, runs a non-dry classical pipeline with local DSP at a short duration and user-selected instrumental mode, then decodes the actual returned streaming WAV. It requires a valid `.wav`, sample rate of at least 22,050 Hz, at least three seconds of audio, one or two channels, finite samples and non-silent amplitude. The test does not count a placeholder, synthetic metadata field or dry-run as a master.

Acceptance: `tests/test_classical_determinism.py` — **3 passed**, including real no-torch end-to-end master generation. Full `pytest tests/ -q` — **233 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**. The regression proves the local CPU baseline only; absent heavyweight AI/TTS/RVC dependencies remain outside this claim.

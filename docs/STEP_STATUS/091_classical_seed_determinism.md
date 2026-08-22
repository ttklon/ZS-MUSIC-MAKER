# PLAN_v39 — ШАГ 091: deterministic classical pipeline seeds

`BeatConstructor` now accepts an optional `seed`. Seeded instances use private Python and NumPy RNGs for sample choices, ghost notes, velocities, hats, noise and stereo panning; two independent runs with the same seed therefore do not depend on global RNG state. Unseeded legacy construction deliberately keeps the prior global RNG behavior, preserving the committed beat golden baseline.

`CyberSynth` accepts/reports seed metadata and explicitly labels its current reproducible scope as `classical_local_dsp_only`. It does not claim that any separate model-based AI stage is deterministic.

Acceptance generated two 8-second seeded classical beats and two 4-second seeded CyberSynth WAVs: each same-seed pair is **byte-for-byte identical**, while changing the beat seed changes the WAV bytes. Existing deterministic beat golden regression stayed green. Full `pytest tests/ -q` — **215 passed**; `compileall` successfully; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

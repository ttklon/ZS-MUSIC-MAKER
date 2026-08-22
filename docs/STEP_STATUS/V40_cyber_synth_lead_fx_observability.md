# APP_L v40 — CyberSynth lead-effects observability

CyberSynth’s FM lead optionally applies Pedalboard chorus, distortion and reverb. A failure in that optional chain previously returned the dry lead with no way to distinguish unprocessed deterministic synthesis from successful effects processing.

The lead chain is now isolated in `_apply_lead_effects()`. Each rendered lead stores additive `last_lead_fx` provenance, and `synthesize_track()` includes it under `lead_fx`. Unavailable or failed effects retain dry FM synthesis with explicit status; the waveform return from `generate_cyber_lead()` remains compatible.

Focused regression verifies that unavailable Pedalboard support retains the exact dry lead and reports `numpy_fm_lead / unavailable`. No Pedalboard effect, external service or rendered artifact was claimed.

Acceptance: focused CyberSynth lead-effects suite — **1 passed**. Full `pytest tests/ -q` — **312 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **89 SILENT_EXCEPT_PASS** (from 90), none in `modules/cyber_synth.py`, and **880 total heuristic records** across **248** Python files. Raw audit JSON remains intentionally ignored.

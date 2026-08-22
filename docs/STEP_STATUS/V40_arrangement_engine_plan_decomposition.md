# APP_L v40 — arrangement-engine plan decomposition

`build_arrangement()` combined genre-specific drum selection, variant energy adjustment, section feature rendering, transition effects and TikTok hook selection. The audit classified the public planner as high complexity despite its deterministic, no-model behavior.

The plan builder now delegates these responsibilities to `_drum_patterns_for_genre()`, `_variant_energy()`, `_transition_fx()`, `_arrangement_section()` and `_tiktok_hook()`. It retains the same genre preference order, seed-controlled random behavior, tempo-scaled section durations, feature fields, 25-second hook bound and returned plan schema.

The focused regression builds two seeded phonk plans and proves exact section/timing determinism, phonk kick/hi-hat selection, transition riser presence, monotonic section timing and valid TikTok hook bounds. It does not load audio, invoke a model or claim generated musical audio.

Acceptance: focused arrangement suite — **1 passed**. Full `pytest tests/ -q` — **279 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **25 HIGH_COMPLEXITY** (from 26), no high-complexity record in `modules/arrangement_engine.py`, **24 LONG_FUNCTION** (from 25), and **878 total heuristic records** across **228** Python files. Raw audit JSON remains intentionally ignored.

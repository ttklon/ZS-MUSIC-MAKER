# PLAN_v39 — ШАГ 096: отчёт legacy-off

Core orchestration now owns a deterministic `LEGACY_CAPABILITY_MANIFEST`. It distinguishes a disabled **versioned compatibility entrypoint** from the availability of the modern core pipeline; the report does not claim that ordinary CPU generation is unavailable. Each entry identifies the v8–v12 module, exported compatibility entrypoint, scope and reason.

`main.py --legacy-off` prints this matrix before every dispatch, including early `--smoke`; it does so through the core manifest and therefore does not import patch modules merely to describe them. A standalone `--legacy-report` prints the same manifest for the requested legacy mode without registration.

Acceptance ran the real `python3 main.py --legacy-off --smoke`: it printed all five disabled compatibility entries and completed its v29 smoke checks with **8 PASS, 0 FAIL**. Missing `mido`, `torch` and TTS engines were reported as honest BLOCKED/fallback behavior, not inferred as successful AI inference. Full `pytest tests/ -q` — **229 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

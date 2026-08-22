# PLAN_v39 — ШАГ 098: терминальный прогресс AI-стадий

`TerminalStageProgress` renders newline-safe progress records without a GUI or external progress package. It receives actual callbacks from `SequentialAIRunner`: each line is based on real stage start/finish events, measured duration, VRAM probes and `StageReport` status. A display callback failure is isolated and cannot fail audio processing.

The AI orchestration API is quiet by default for library callers. `main.py --ai` and `main.py --ai --dry-run` explicitly enable progress for all twelve configured stages. Final states are differentiated as `OK`, `FALLBACK`, `SKIPPED` or `FAILED`; a fallback status is not presented as an available-model render.

Acceptance ran the live `python3 main.py --ai --dry-run` flow and captured **12 START** and **12 finish** lines. The final live record was `12/12 FALLBACK tag | 0.01s | VRAM 0.000->0.000 GB`, accurately reflecting absent optional model dependencies rather than pretending inference occurred. The generated backup was removed after verification. Full `pytest tests/ -q` — **232 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

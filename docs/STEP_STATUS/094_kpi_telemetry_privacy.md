# PLAN_v39 — ШАГ 094: KPI telemetry without PII

`modules/hit_kpi_monitor_v11.py` now persists `zsmm.kpi-telemetry.v1` JSONL records built from an explicit allowlist: pipeline duration, detector percentage, final verdict, and per-stage duration, VRAM, score and status. Project IDs, stage notes, lyric text, prompts, release paths and filenames are not included. Stage labels must match a short identifier allowlist; any unsafe label is persisted as `redacted`.

`modules/kpi_dashboard_v12.py` reads only the latest valid v1 telemetry record and renders aggregate stage metrics. Legacy or malformed history lines are ignored. The dashboard telemetry section therefore has no route to expose free-form session fields.

Acceptance injected a private project path and lyric-like note, persisted telemetry, and asserted the raw JSONL contains none of the path/text while retaining expected metrics. It also verified safe dashboard rendering of duration, VRAM and score. Full `pytest tests/ -q` — **222 passed**; `compileall` successfully; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

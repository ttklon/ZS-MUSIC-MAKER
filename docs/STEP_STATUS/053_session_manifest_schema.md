# PLAN_v39 — ШАГ 053: сохранение AI сессий и manifest schema

Каждый запуск `run_ai_pipeline()` теперь сохраняет `output/<project>/manifest.json` со **schema_version=1**. Manifest содержит project ID, generator, wizard state, полный stage report, engine/file/Hugging Face provenance всех 13 AI roles и artifact map. Он отделён от совместимого `project_meta.json`, что позволяет versioned session consumers ориентироваться на стабильный контракт.

Regression запускает AI dry pipeline в temporary project root и проверяет schema v1, project ID, stage list, все 13 role records и cover artifact map. На момент приёмки: `pytest tests/test_ai_layer.py -q` — **32 passed**; полный `pytest tests/ -q` — **119 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**.

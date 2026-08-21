# PLAN_v39 — ШАГ 076: data/prompts и текущие AI-роли

До шага все 15 `.prompt.txt` находились только в versioned data и упоминались лишь планом; код их не читал. `app/ai/prompts.py` теперь содержит явный allowlisted `PROMPT_ASSETS` catalog. Каждый файл однозначно назначен одной текущей роли/подсистеме: lyrics (4), metadata (8), analysis (1), cover_art (1), trend_analysis (1). `load_prompt_asset()` не принимает произвольный path; `render_prompt_asset()` рендерит documented placeholders с defaults; `validate_prompt_catalog()` обнаруживает unmapped/missing/unrenderable asset.

Runtime builders для lyrics, dossier analysis и metadata включают role assets. Cover builder активирует и валидирует cover asset, сохраняя совместимый concise SDXL-facing output. Public names и сигнатуры builders сохранены. Никакой LLM/SDXL inference не запускался: integration проверяет templates и contracts, а heavy runtimes остаются environment-dependent.

Приёмка: new catalog tests — 4 passed; каждый из 15 versioned prompt files mapped и успешно rendered, unknown/path-traversal name отклонён. Полный `pytest tests/ -q` — **171 passed**; `compileall` успешно; AST-аудит — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

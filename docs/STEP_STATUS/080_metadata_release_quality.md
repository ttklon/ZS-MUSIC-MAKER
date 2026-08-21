# PLAN_v39 — ШАГ 080: metadata release quality gate

`validate_metadata_json()` теперь проверяет release metadata объективно: title 3–80 characters; обе `spotify_desc` и `youtube_desc` 20–400 characters; максимум восемь tags across `tags_*`; tags непустые и unique after case/hash normalization; запрещены явные AI filler terms. Metrics сохраняют title length, description lengths, tag/unique tag counts и forbidden hits; invalid output возвращает actionable reason.

`stage_metadata` использует `_metadata_fallback()`. Genre/theme/mood fallback создаёт title, две достаточно длинные descriptions и шесть уникальных tags. Поэтому dry-run, missing metadata LLM и rejected LLM JSON проходят только после того же validator-а; source/reason/quality сохраняются в `metadata.json`.

Приёмка: boundary tests покрыли valid baseline, duplicate/too-many tags, forbidden term, short description и dry-run artifact. Focused metadata suite — 39 passed. Полный `pytest tests/ -q` — **185 passed**; `compileall` успешно; AST-аудит — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**. Metadata LLM runtime/weights не запускались.

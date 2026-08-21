# PLAN_v39 — ШАГ 079: artist dossier schema и migration

Добавлен versioned `data/artist_dossier/schema.json` (v1). Schema определяет required rich artist fields: `bio`, `themes`, `slang`, `flow`, `analogs`, compatibility aliases (`core_themes`, `lexicon`), `signature_tricks`, `avoid` и `schema_version=1`. `.gitignore` разрешает только этот schema file; generated runtime dossiers остаются ignored.

`DossierManager` теперь загружает versioned schema, нормализует compatible aliases, валидирует complete dossier при aggregation/save и добавляет `schema_version`. Новый incomplete completed payload отклоняется с понятным `ValueError`; legacy incomplete artist JSON при чтении мигрирует в explicit `deferred` dossier с reason, а не выдаётся за completed content. Existing no-model `note`/deferred outputs остаются честными и не проходят completed-schema validation.

Приёмка: четыре tests проверили schema, valid normalized payload, incomplete rejection, legacy deferred migration и save-time guard. Полный `pytest tests/ -q` — **184 passed**; `compileall` успешно; AST-аудит — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**. Реальный analysis LLM не выполнялся.

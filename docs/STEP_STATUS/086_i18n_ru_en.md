# PLAN_v39 — ШАГ 086: RU/EN i18n foundation

Created `app/core/i18n.py` with versioned RU/EN dictionaries, `t(key, **values)`, safe missing-key/format fallback, language introspection and an immediate process-local `set_language()` switch. No restart is required. `Settings` now reads `ZSMM_LANGUAGE` from environment or `.env` and reports it through `dump()`.

The existing wizard uses translations for its navigation controls and Help/AI menu labels while retaining the original action wiring. `pipeline_core` emits translated lifecycle/stage display strings and returns `display_status`; stable machine-readable `status` remains exactly `completed` or `failed`.

Acceptance covers runtime EN→RU switching, interpolation, invalid-language rejection, `.env` language loading and translated completed pipeline display status. Full `pytest tests/ -q` — **201 passed**; `compileall` successfully; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

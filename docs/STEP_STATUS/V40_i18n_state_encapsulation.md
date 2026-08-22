# APP_L v40 — i18n language-state encapsulation

The final `GLOBAL_STATEMENT` finding was the mutable `_current_language` scalar in the process-local i18n module. It was protected by a lock, but required `global` assignment and made the state ownership implicit.

The module now stores the active language in a private `_LanguageState` dataclass instance. `set_language`, `get_language` and `t` retain their existing lock-based behavior and public API; only internal state ownership changed. The existing RU/EN switching, safe missing-key fallback, dotenv language loading and translated pipeline-status tests all pass.

A fresh audit now reports **0 `GLOBAL_STATEMENT` findings**. Current remaining heuristic categories are `BARE_PRINT`, docstrings, silent fallback handlers, complexity/long functions and a bounded set of remaining sleeps; none are declared completed by this change.

Acceptance: targeted i18n tests — **4 passed**. Full `pytest tests/ -q` — **251 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

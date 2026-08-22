# APP_L v40 — GLOBAL_STATEMENT: settings cache

`config.settings` previously maintained a mutable module-level `_settings` value through `global` assignments. The public contract did not require mutable global state: callers need one lazy process-local settings snapshot and tests need a deterministic reset.

`get_settings()` now uses `functools.lru_cache(maxsize=1)`, while `reset_settings()` uses `get_settings.cache_clear()`. The public function names, lazy loading behavior and reset semantics are preserved. A new regression proves that the cached environment-derived value remains stable until reset and reloads the changed environment after reset.

The other currently triaged global statements—process-local i18n language and mastering optional-backend capability fallbacks—remain intentionally open because changing their behavior requires separate concurrency and DSP fallback analysis.

Acceptance: targeted settings tests — **7 passed**. Full `pytest tests/ -q` — **248 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

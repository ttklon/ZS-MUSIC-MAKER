# PLAN_v39 — ШАГ 084: RenderQueue cancel, priority и persistence

`RenderQueue` now persists state to `output/queue/queue.json`; a read-only compatibility fallback accepts a previous `queue_state.json`. Persistence creates the parent directory only when writing. `QueueItem` records `priority` and `created_at`; higher numeric priority is selected first and original list order remains the deterministic FIFO tiebreak for equal priority.

The API accepts `enqueue(recipe, priority=...)`, recipe-level priority and `set_priority()` for pending work. Pending cancellation remains terminal. On restart, a non-cancelled running item is safely reset to pending with stage/progress cleared; a running item with `cancel_requested` becomes terminal `cancelled` rather than being resurrected.

Acceptance includes a three-item persisted scenario: the middle item is cancelled, the last receives highest priority, an active first item is persisted, and a newly constructed queue restores the first as pending while preserving cancellation and next-item priority. Existing FIFO and running-stage cancellation tests remain green. Full `pytest tests/ -q` — **194 passed**; `compileall` successfully; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

# APP_L v40 — interruptible idle worker waits

Two worker loops used uninterruptible idle `time.sleep` calls: the desktop runtime worker waited up to 0.2 seconds and the persistent render queue waited up to three seconds after a stop request. This made shutdown responsiveness depend on polling timing.

Both loops now call their existing `threading.Event.wait(timeout)` instead. The timeout preserves the prior idle poll cadence, while setting the stop event wakes the worker immediately. `RuntimeOrchestrator` also now provides a bounded public `stop(join_timeout=1.0)` lifecycle method, matching the render queue’s stop capability.

The regression starts both workers while idle, invokes their stop paths, joins them with bounded timeouts and verifies that both have exited in under 0.5 seconds. No audio pipeline is started by the test.

Acceptance: targeted worker/queue tests — **4 passed**. Full `pytest tests/ -q` — **250 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

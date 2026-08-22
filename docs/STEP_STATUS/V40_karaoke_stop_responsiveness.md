# APP_L v40 — karaoke stop responsiveness

`KaraokeSession._run()` used uninterruptible `time.sleep` for count-in beats and 20 ms polling. A stop request during a wait could be delayed by the full beat duration; the worker then continued to its natural completion code and could overwrite the caller-set `stopped` state with `finished`.

Both waits now use the session’s existing stop event. A set event returns immediately from the worker, preserving `stopped`; an unset event waits for the same beat or polling duration, so timing callbacks are unchanged during normal playback.

The regression creates a one-minute count-in, waits for its first beat, requests stop and verifies that the worker exits in under 0.5 seconds with state `stopped`. It does not access a microphone or render audio.

Acceptance: focused karaoke stop test — **1 passed**. Full `pytest tests/ -q` — **253 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

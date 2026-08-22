# APP_L v40 — cancellable voice-onboarding recording

`record_step()` performed a real-microphone capture by unconditionally sleeping for the target duration. A caller could not cancel a 60-second karaoke step or any other onboarding recording once the microphone stream had started.

The public function now accepts an optional `threading.Event`. It waits for the same target duration when unset, but a set event wakes it immediately, stops the recorder, marks the step `cancelled`, and leaves `ok` false. If the recorder returns partial metadata during shutdown, it is retained for diagnostics but cannot advance onboarding progress: `compute_progress()` now totals only accepted, non-cancelled steps. Existing callers remain compatible because the new parameter is optional and no caller supplied a third argument.

The focused regression uses a fake recorder and an already-set event. It verifies immediate recorder finalization, `cancelled=True`, `ok=False`, retained partial metadata, and zero accepted progress. No microphone, audio device or vault file is accessed.

Acceptance: focused onboarding cancellation and manifest suite — **2 passed**. Full `pytest tests/ -q` — **259 passed**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit records **7 BLOCKING_SLEEP** findings (from 8), no blocking-sleep record in `modules/voice_onboarding.py`, and **904 total heuristic records** across **218** Python files. The generated raw audit JSON remains intentionally ignored.

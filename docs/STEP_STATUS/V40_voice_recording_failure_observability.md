# APP_L v40 — voice-recording failure observability

The microphone recorder intentionally prevents callback/metrics/shutdown exceptions from escaping into a real-time audio path. Previously, three `except: pass` handlers preserved that availability policy but discarded the failure reason completely.

`RealMicRecorder` now exposes `last_error`. `_callback`, `_emit_metrics`, and stream shutdown record a contextual exception string while remaining non-fatal. This avoids logging on every audio frame and leaves microphone capture behavior unchanged, while giving an owner or UI code a concrete diagnostic to inspect after a degraded recording attempt.

The focused regression forces a metrics consumer failure and a stream-stop failure. It verifies no exception escapes, the stop result remains the compatible `no audio captured` fallback, and `last_error` identifies the exact failing path. The existing real temporary-WAV split regression also remains green.

Acceptance: focused recorder suite — **3 passed**. Full `pytest tests/ -q` — **262 passed**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit records **116 SILENT_EXCEPT_PASS** (from 119), leaving two unrelated I/O fallback handlers in `modules/voice_recording.py`; **895 total heuristic records** across **219** Python files. No inference or microphone device claim was made; raw audit JSON remains intentionally ignored.

# APP_L v40 — voice-recording I/O observability

The last two `SILENT_EXCEPT_PASS` handlers in `modules/voice_recording.py` concealed different I/O outcomes. Failed take-manifest writing discarded its cause while still returning the split takes. Failed sounddevice enumeration made the recorder appear to have no devices without explaining whether the backend query itself failed.

Manifest persistence now emits a warning but still returns the successfully generated `TakeInfo` list. `capability_report()` now includes `device_query_error`: `None` when discovery completes or a typed error string when the backend query fails. It continues to report zero usable input devices and `real_recording_possible=False` on discovery failure; no false recording capability is claimed.

Focused regressions force a device-service exception and a manifest-write `OSError`. They verify the explicit capability diagnostic, preserved non-recording capability state, retained takes, and warning emission. The recorder callback/shutdown and WAV split tests remain green.

Acceptance: focused recorder suite — **5 passed**. Full `pytest tests/ -q` — **264 passed**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit records **114 SILENT_EXCEPT_PASS** (from 116) and **0** such records in `modules/voice_recording.py`; **894 total heuristic records** across **219** Python files. The generated raw audit JSON remains intentionally ignored.

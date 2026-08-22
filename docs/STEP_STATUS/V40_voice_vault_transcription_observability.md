# APP_L v40 — Voice Vault transcription observability

Voice Vault supports two optional transcription backends, `faster_whisper` and `whisper`. Previously, failures in both backend attempts were silently suppressed and an indexed voice recording simply contained no transcript. That outcome did not distinguish an unrequested transcript, an unavailable package, a model-cache failure or an empty backend result.

The intake flow now uses `_transcribe_with_diagnostics()`, which records every attempted backend. A successful backend reports its engine; each failed backend records its typed error and emits an operational warning. `add_recording(..., transcribe=True)` persists this additive `transcription` metadata with the existing `transcript` and coverage fields. For callers that use only the legacy text API, `_transcribe()` remains compatible. A non-requested transcript is labelled `not_requested`.

Focused regressions inject two unavailable backends and confirm both attempts are preserved, warnings are emitted and no transcript is fabricated. They also verify that the persisted Voice Vault entry carries the diagnostics. No Whisper model was loaded and no transcription output is claimed.

Acceptance: focused Voice Vault transcription suite — **2 passed**. Full `pytest tests/ -q` — **293 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **103 SILENT_EXCEPT_PASS** (from 105), none in `modules/voice_vault_v9.py`, and **878 total heuristic records** across **236** Python files. The raw audit JSON remains intentionally ignored.

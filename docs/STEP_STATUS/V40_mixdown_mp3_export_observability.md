# APP_L v40 — mixdown optional MP3-export observability

`master_with_matchering_status()` previously swallowed every MP3 conversion failure after producing a WAV master. The WAV could still be valid, but callers could not distinguish a successful 320k MP3 export from an unavailable encoder or a write failure.

The optional export is now isolated in `_export_optional_mp3()`. The status response preserves the WAV-master contract and adds `mp3_export`: success reports the MP3 path, while failure reports `ok: false`, no MP3 path and the exception text. A warning is emitted for operational diagnostics. `full_mixdown()` passes this structured state through and continues to expose `master_mp3` as `None` when no MP3 was created. This does not claim a failed MP3 encoder produced an audio artifact, and it does not alter Matchering-versus-copy fallback truthfulness.

Focused tests simulate missing Matchering and use a fake MP3 encoder. They verify successful compatible WAV-copy plus MP3 creation, and a simulated encoder failure that leaves the WAV output available while returning explicit `mp3_export` diagnostics. No actual mastering, media encoding, model inference or optional backend is claimed.

Acceptance: focused mixdown suite — **2 passed**. Full `pytest tests/ -q` — **287 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **107 SILENT_EXCEPT_PASS** (from 108), none in `modules/mixdown.py`, and **878 total heuristic records** across **233** Python files. The raw audit JSON remains intentionally ignored.

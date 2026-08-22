# APP_L v40 — Artist Dossier audio-copy observability

`DossierManager.add_track()` tries to archive a supplied audio file under the artist dossier. Previously, an archive-copy failure was swallowed. The returned track retained the original source path with no indication that the managed dossier copy was missing. In addition, direct `add_track()` usage had not created the destination `audio/` directory, causing an avoidable copy failure that was hidden by that exception handler.

`TrackEntry` now persistently exposes additive `audio_copy` diagnostics. Successful copies report their source and archived path. A failed copy retains the source-path compatibility behavior for downstream analysis, but explicitly records the intended archive path and typed error; it does not claim a local dossier artifact exists. Missing sources are labelled `source_missing`. The intake flow now creates the archive directory before attempting a valid direct copy.

Focused regressions use a real temporary WAV-like file to prove direct intake creates and persists the archived copy. A simulated `disk full` failure proves the original source remains usable while serialized diagnostics report the failed archive transfer. No audio analysis, optional model execution or media generation is claimed.

Acceptance: focused Artist Dossier audio-copy suite — **2 passed**. Full `pytest tests/ -q` — **295 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **102 SILENT_EXCEPT_PASS** (from 103), none in `modules/artist_dossier/manager.py`, and **879 total heuristic records** across **237** Python files. The raw audit JSON remains intentionally ignored.

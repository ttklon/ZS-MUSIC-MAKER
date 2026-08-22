# APP_L v40 — release-export decomposition

`export_release()` combined artist fallback, master/instrumental/acapella copying, listening-stand copying, release documents, metadata/ISRC creation, artifact hashing and ZIP assembly. The first document/archive extraction preserved behavior but left the public method above the deep-audit complexity threshold, so the refinement continued rather than being falsely closed.

The final structure delegates artist resolution, generic variant conversion, master/instrumental/acapella packaging, listening-stand packaging, release documents and archive finalization to focused helpers. The public entry point retains its ordered contract and returned `files` map. Master and instrumental tags remain attempted only when the converted MP3 exists; audio conversion remains subject to its existing capabilities and no unavailable encoder is claimed successful.

The existing release-export regression was expanded and passed. It uses a temporary WAV, validates the public result, ZIP, SHA-256 manifest fingerprint, generated ISRC, lyrics/recipe/metadata CSV/release-note file entries and release-note artist content. It does not invoke a model or make a distribution upload.

Acceptance: focused release-export suite — **1 passed**. Full `pytest tests/ -q` — **274 passed**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **30 HIGH_COMPLEXITY** (from 31), no high-complexity record in `modules/release_export.py`, **28 LONG_FUNCTION** (from 29), and **882 total heuristic records** across **224** Python files. Raw audit JSON remains intentionally ignored.

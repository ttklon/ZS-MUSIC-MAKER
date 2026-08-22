# APP_L v40 — Voice Vault index recovery observability

The persistent Voice Vault index is user metadata. `_load_index()` previously caught every parse/read failure and returned an empty index without evidence. A later write could therefore replace the effective in-memory view of a corrupt file with no indication of why the vault appeared empty.

The loader now catches only `OSError` and `json.JSONDecodeError`, logs a warning with the failure reason, and returns the same compatible empty-index shape. Missing index files remain normal first-run behavior. Optional Whisper transcription fallbacks remain untouched and are still honestly unavailable when their model packages are absent.

The focused regression redirects `INDEX_FILE` to malformed temporary JSON and verifies both the unchanged `{"items": {}}` fallback and the warning. It does not access the repository voice vault or run any model.

Acceptance: focused Voice Vault suite — **3 passed**. Full `pytest tests/ -q` — **265 passed**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit remains at **114 SILENT_EXCEPT_PASS** and **894 total heuristic records** across **220** Python files. The count is unchanged because the prior handler returned a value rather than being an `except: pass` record; this package improves user-data diagnostics, not that narrow heuristic count. Raw audit JSON remains intentionally ignored.

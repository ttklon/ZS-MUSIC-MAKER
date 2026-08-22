# APP_L v40 — Lyric Vault JSONL recovery observability

The Lyric Vault loader previously ignored malformed JSONL lines through a silent exception handler. Valid memory entries remained usable, but callers had no way to distinguish an empty history from damaged local data.

`_load_lyric_memory_with_errors()` now keeps valid entries and captures typed line-level JSON decode diagnostics. The historical list-only `_load_lyric_memory()` and `get_lyric_memory()` contracts remain intact. A new `get_lyric_memory_diagnostics()` accessor returns recent valid memories together with `read_errors` for callers that need recovery evidence.

The focused regression uses a temporary JSONL file with two valid records and one malformed line. It verifies reverse chronological valid-memory output through both APIs and an explicit `line 2: JSONDecodeError` diagnostic. It does not modify the repository Lyric Vault or invoke Ollama, trend scout, LLMs or models.

Acceptance: focused Lyric Vault suite — **1 passed**. Full `pytest tests/ -q` — **283 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **109 SILENT_EXCEPT_PASS** (from 110). The selected memory-loader record is removed; the separate intentional local Ollama optional-probe fallback in `modules/lyrics_gen.py` remains and is not claimed resolved. Total heuristic records remain **877** across **231** Python files. Raw audit JSON remains intentionally ignored.

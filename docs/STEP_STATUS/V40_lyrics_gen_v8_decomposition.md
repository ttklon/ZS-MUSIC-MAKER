# APP_L v40 — lyrics-v8 orchestration and marker decomposition

`lyrics_gen_v8` concentrated optional trend retrieval, author-style lookup/ingestion, v7 generator compatibility fallbacks, bilingual hook insertion and final section assembly in `generate_lyrics_v8()`. Its section parser separately concentrated six Russian/English marker branches. Both were confirmed high-complexity audit findings.

The public generator now orchestrates `_fetch_slang()`, `_author_style_prompt()`, `_generate_raw_lyrics()`, `_ensure_bilingual_chorus()` and `_assemble_lyrics_text()`. The parser now uses the ordered `_SECTION_MARKERS` map through `_section_for_marker()`. The user-visible seed rules, fallback lyric text, section ordering, bilingual default hook, response keys, author metadata and deprecated import behavior remain intact.

Focused regression replaces all optional helpers with deterministic fakes, proving normalized user words, slang/seed construction, style prompt propagation, section output, chorus metadata and backing flag. The pre-existing deprecation test remains green. No trend scout, author ingestion, external source, LLM or model inference is invoked.

Acceptance: focused lyrics-v8 plus legacy adapter suite — **5 passed, 1 expected deprecation warning**. Full `pytest tests/ -q` — **278 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **26 HIGH_COMPLEXITY** (from 28), no high-complexity record in `modules/lyrics_gen_v8.py`, and **879 total heuristic records** across **227** Python files. The raw audit JSON remains intentionally ignored.

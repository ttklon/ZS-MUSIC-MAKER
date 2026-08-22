# APP_L v40 — Video Editor LRC parsing observability

Video Editor accepts LRC lyric timing files for subtitle cues. Earlier, malformed timestamp candidates were silently skipped, so a partially malformed file could yield fewer subtitles without any structured indication of the dropped entry.

`_parse_lrc_with_diagnostics()` now returns parsed cues plus additive diagnostics. It records unterminated tags, malformed timestamp candidates and source-reading failures. The existing `_parse_lrc()` remains a compatible cue-list wrapper for current subtitle callers. Valid timestamps retain their sorted cue-list semantics even when other entries are malformed.

Focused regressions cover a valid multi-timestamp line with a malformed timestamp candidate, plus an unreadable source path. They do not invoke MoviePy, render video, encode media or claim a generated subtitle artifact.

Acceptance: focused suite — **2 passed**. Full `pytest tests/ -q` — **323 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**; `git diff --check` successful. Fresh deep audit reports **83 SILENT_EXCEPT_PASS** (from 84) and **878 total heuristic records** across **254** Python files. Raw audit JSON remains ignored and was not committed.

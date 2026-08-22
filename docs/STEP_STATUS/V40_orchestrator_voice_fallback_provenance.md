# APP_L v40 — orchestrator voice-synthesis fallback provenance

Voice synthesis attempts the optional `voice_synth` module before falling back to `pyttsx3` and, if needed, the explicitly blocked synthetic scaffold. The recovery chain is intentional, but module availability, failed `synth()` calls and unusable `synth`/`synthesize` outputs were previously discarded before the fallback result.

`_stage_voice_synth()` now returns additive `fallback_attempts` provenance for an unavailable module, exceptions from `synth()` or `synthesize()`, and unusable primary or secondary output. It preserves successful primary returns and the established pyttsx3/scaffold fallback contract. This makes a fallback distinguishable from a successful optional voice-engine run without representing the scaffold as real vocals.

The focused regression uses a mock voice module that raises from `synth()` and yields unusable secondary output; the fallback speaker helper is mocked. No TTS engine, synthetic scaffold, audio file, model inference or vocal artifact was run or claimed.

Acceptance: focused suite — **1 passed**. The first full-suite attempt exposed a test-double package-binding issue, which was corrected without changing production behavior; the final full `pytest tests/ -q` run — **329 passed, 1 expected deprecation warning**. `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**; `git diff --check` successful. Fresh deep audit reports **78 SILENT_EXCEPT_PASS** (from 79) and **881 total heuristic records** across **257** Python files. `MISSING_DOCSTRING` is **322** due to the concise focused test function; raw audit JSON remains ignored and was not committed.

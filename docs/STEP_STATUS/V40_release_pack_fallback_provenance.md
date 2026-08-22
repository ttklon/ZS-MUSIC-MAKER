# APP_L v40 — release-pack fallback provenance

The main pipeline attempts the full release pack, then legacy v13 packaging, and finally a minimal release pack. The fallback itself is deliberate, but upstream failures were previously discarded; a caller could only see the generic minimal-pack reason or a legacy result without knowing which earlier engine had failed.

`_stage_release_pack()` now retains additive `fallback_attempts` provenance whenever an earlier packer fails, returns an invalid result, lacks the legacy `build_pack` entry point, or both engines fail before minimal packaging. Each record identifies the engine, status and typed error. A successful full-pack dictionary still returns unchanged, and existing fallback result fields remain available.

Focused regressions simulate a full-pack failure followed by legacy success, then full and legacy failures followed by the minimal pack. They use mocked packers only; no WAV is copied, no MP3 is encoded, no cover is created, and no release archive or media artifact is claimed.

Acceptance: focused suite — **2 passed**. Full `pytest tests/ -q` — **326 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**; `git diff --check` successful. Fresh deep audit reports **80 SILENT_EXCEPT_PASS** (from 82), **878 total heuristic records** across **255** Python files. `MISSING_DOCSTRING` is **319** because the two deliberately added test functions are public by the heuristic; raw audit JSON remains ignored and was not committed.

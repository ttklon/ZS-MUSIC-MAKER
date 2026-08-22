# APP_L v40 — RVC progress-parser observability

RVC subprocess progress parsing previously swallowed malformed epoch output. The training job correctly avoided updating progress when parsing failed, but the operator had no evidence that a backend emitted unusable progress text.

`RVCTrainer` now records typed `progress_parse_errors` for malformed epoch tokens and retains the existing job progress until a real epoch is parsed. This does not alter process exit handling, train a model, or claim successful backend progress.

Focused regression supplies a successful fake subprocess with malformed `Epoch ???/10` output. It proves progress remains `0.0` and the parse failure is recorded.

Acceptance: focused RVC parser suite — **1 passed**. Full `pytest tests/ -q` — **310 passed, 1 expected deprecation warning**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **91 SILENT_EXCEPT_PASS** (from 92). The selected parser record is removed; the three remaining RVC records are optional CUDA/DirectML/ROCm capability probes. The audit reports **882 total heuristic records** across **246** Python files. Raw audit JSON remains intentionally ignored.

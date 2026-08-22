# APP_L v40 — voice-synth honesty and decomposition

`modules/voice_synth.py` concentrated output verification, candidate ordering, fallback handling and directory creation in a high-complexity `synth()` function. Backend failures were emitted through bare `print`, and an output-directory creation failure was silently swallowed before the code attempted unavailable backends.

The module now uses structured module logging. `_produced()` verifies the actual non-empty output file, while `_run_candidates()` centralizes ordered backend attempts. `synth()` retains the established priority and fallback order, returns an output path only after verification, returns `""` when no engine can produce audio, and explicitly logs an unavailable output directory. It does not claim that Silero, XTTS, Bark, pyttsx3 or gTTS ran in this sandbox.

Focused tests replace all synthesizers with deterministic fakes. They verify the female Silero speaker choice and verified primary output, XTTS-to-Silero fallback order, and the logged honest empty result when every fake backend fails. No heavy TTS model, system TTS service or network TTS is invoked.

Acceptance: focused voice-synth suite — **3 passed**. Full `pytest tests/ -q` — **268 passed**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. Fresh deep audit reports **34 HIGH_COMPLEXITY** (from 35), **317 BARE_PRINT** (from 325), **113 SILENT_EXCEPT_PASS** (from 114), and **886 total heuristic records** across **221** Python files. The one remaining `voice_synth` bare print is its explicit `__main__` CLI output; raw audit JSON remains intentionally ignored.

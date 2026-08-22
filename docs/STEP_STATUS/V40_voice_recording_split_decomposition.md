# APP_L v40 — voice-recording split decomposition

`split_wav_into_takes()` was a **117-LOC** production function, exceeding the deep-audit long-function threshold of 100 LOC. It combined WAV loading, 20 ms RMS framing, silence-state tracking, per-take signal metrics/quality, WAV persistence and manifest writing in one body.

The public function is now an orchestration layer. `_read_mono_wav()` owns safe WAV loading/channel reduction, `_frame_rms_db()` owns frame analysis, and `_write_take()` owns duration filtering, metrics/quality calculation and take-file persistence. The public API, 20 ms framing, -40 dB silence threshold, `min_silence_ms` and `min_take_ms` semantics, take metadata and manifest name remain unchanged.

The regression writes a real temporary WAV with two voiced one-second regions separated by 700 ms of silence. It verifies two persisted takes, the supplied style, valid durations and a manifest whose IDs match returned `TakeInfo` values. No microphone or unavailable sounddevice backend is invoked.

Acceptance: focused voice-split test — **1 passed**. Full `pytest tests/ -q` — **254 passed**; `compileall` successful; AST dead-import audit — **0**; data inventory — **73 managed, 0 unknown, 0 invalid**. A freshly regenerated deep audit reported **29 LONG_FUNCTION** records (from 30 before this package), **909 total issues** across **215** Python files, and verified no `LONG_FUNCTION` record for `modules/voice_recording.py`. The raw audit JSON remains intentionally ignored.

# PLAN_v39 — ШАГ 071: golden-тесты звука

Добавлены versioned WAV fixtures в `tests/fixtures/audio/` и explicit `.gitignore` exception только для `golden_*.wav`; runtime WAV outputs остаются ignored. `tools/generate_audio_goldens.py` воспроизводимо создаёт 15-second stereo beat fixed-seed fixture и 10-second stereo master fixture на доступной `BeatConstructor`/`ProAudioDSP` цепочке. `tools/audio_golden_metrics.py` вычисляет стабильные метрики: sample rate, channels, duration, RMS, peak, stereo correlation и spectral centroid.

Golden baseline: beat — 15.000 s, 44.1 kHz stereo, RMS 0.07419, centroid 10,326 Hz, correlation 0.84298; master — 10.000 s, 44.1 kHz stereo, RMS 0.35481, peak 0.73160, centroid 291.34 Hz. Tests допускают узкие metric tolerances и повторно рендерят fixed-seed audio, поэтому ловят material DSP drift без brittle byte-for-byte comparison.

`matchering` runtime отсутствует в sandbox; этот шаг **не** утверждает Matchering dry master. Golden master покрывает реально выполнимый `ProAudioDSP` baseline. Приёмка: focused golden tests — **8 passed**; полный `pytest tests/ -q` до ignore policy correction — **148 passed**; AST-аудит — **0 dead imports**. После exception fixtures стали видимыми для Git и focused tests были повторно зелёными.

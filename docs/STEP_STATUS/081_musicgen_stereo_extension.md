# PLAN_v39 — ШАГ 081: MusicGen stereo intro/outro extension

Добавлен `extend_beat_with_stereo_sections()` в `app/core/orchestrator_ai.py`. Helper читает base beat и generated intro/outro WAV, приводит mono/stereo к двухканальному output, resamples intro/outro к base sample-rate, применяет equal-power crossfade на обеих границах и peak-normalizes до 0.98. Результат сохраняется отдельным `beat_stereo_extended.wav`.

`stage_music_stereo` теперь при доступном handle и valid base beat рендерит отдельные stereo intro/outro, валидирует каждый через existing stereo gate, расширяет beat и публикует `beat_path`. `stage_mix` предпочитает этот extended path; при missing model/base/generation/quality/extension failure возвращается explicit skipped/fallback и исходный beat не заменяется. Dry-run остаётся skipped; real MusicGen не симулируется.

Приёмка использовала реальные temporary WAV (base 8 kHz, intro 4 kHz, outro 16 kHz): output stereo 8 kHz, finite, peak <= 0.981 и duration ~6 s для 2+4+2 s sections с двумя 1-second overlaps. Missing input returns an actionable failure. Полный `pytest tests/ -q` — **187 passed**; `compileall` успешно; AST-аудит — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**. MusicGen/audiocraft weights остаются BLOCKED в sandbox.

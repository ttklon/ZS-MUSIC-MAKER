# PLAN_v39 — ШАГ 045: beat_gen_ai как основная stage_music ветвь

## Integration contract

Inline MusicGen code удалён из `stage_music`. При доступной роли `music_generation` стадия строит prompt из genre/BPM/key/mood и dossier features, затем вызывает единую тестируемую точку `modules.beat_gen_ai.render_beat_ai(..., handle=handle)`. Handle приходит от `SequentialAIRunner`, поэтому adapter не открывает вложенный `registry.use()` и runner сохраняет ответственность за выгрузку модели.

| Поведение | Реализация |
|---|---|
| Chunk rendering | Максимум 30 s на один вызов, default 20 s; длительный трек собирается из chunks. |
| Continuation | Используется `generate_continuation` при доступности API; при несовместимости продолжения следующий independent chunk — явный technical fallback, не скрытая ошибка. |
| Duration integrity | Adapter отказывает, если generator вернул меньше samples, чем запрошено. Избыток ровно обрезается до `duration_sec × sample_rate`. |
| Loudness safety | Peak ограничивается до 0.98 до записи PCM_16; после adapter stage применяет существующий audio quality gate. |
| No MusicGen | Сохраняется `CyberSynth` fallback с тем же post-render audio gate и `engine=cyber_synth_fallback`. |
| Reference audio | `reference_wav` передаётся и записывается как provenance. Current MusicGen adapter не имеет подтверждённого audio-conditioning API, поэтому `reference_applied=False` и это не выдаётся за style transfer. |

## Evidence

Fake MusicGen tests проверяют runner-handle path, два 1 s chunks, exact 2.0 s output, stereo WAV, peak ниже 0.99, reference provenance и честный отказ при недостатке generated samples. На момент приёмки: `pytest tests/test_ai_quality.py -q` — **35 passed**; `pytest tests/ -q` — **113 passed**; AI dry-run — успешно; `compileall` — успешно; AST-аудит — **0 dead imports**.

> `audiocraft`, `torch` и MusicGen weights отсутствуют в sandbox. Real MusicGen inference остаётся **BLOCKED**; adapter/chunk/quality contracts проверены без тяжёлых зависимостей.

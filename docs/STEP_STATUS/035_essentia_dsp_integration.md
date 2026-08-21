# PLAN_v39 — ШАГ 035: интеграция essentia/librosa DSP

## Реализованный контракт

Dossier feature stage переведена с неявного pure-DSP блока на зарегистрированную optional-роль `essentia`. Функция `extract_dsp_features()` извлекает BPM, tonal key, duration и RMS с engine marker. Если DSP-role недоступна, stage сохраняет reference audio без несуществующих метаданных и возвращает explicit `skipped`.

| Сценарий | Поведение |
|---|---|
| Есть audio и зарегистрированный DSP handle | Извлекаются `bpm`, `key`, `duration_sec`, `loudness_rms`, `engine`. |
| Входной файл пуст | Возвращается `DSP input audio is empty`. |
| DSP dependency недоступна | Возвращается `skipped: essentia/librosa unavailable`. |
| Извлечение завершилось исключением | Возвращается `ok=False` с `DSP feature extraction failed`. |

## Доказательства

Во время приёмки sandbox не содержал `librosa`, хотя пакет закреплён в `requirements.txt`; зависимость восстановлена именно из проектного requirements. После этого реальный 4-секундный WAV прошёл обработку и вернул duration и RMS, а полный набор дал `pytest tests/` — **84 passed**, `compileall` — успешно, AST-аудит — **0**.

> В текущем реестре роль названа `essentia`, но фактический base-runtime — `librosa_dsp`; это явно возвращается в `engine` и не маскируется как Essentia TensorFlow.

# PLAN_v39 — ШАГ 036: метрики, fallback и валидация essentia/librosa DSP

## Quality contract

`validate_dsp_features()` проверяет полноту DSP metadata и музыкальную допустимость результатов. Для использования в dossier должны существовать корректные BPM, key, duration и RMS; иначе feature-stage возвращает failure и сохраняет reference audio без ненадёжных метаданных.

| Метрика | Допустимое условие | Причина отказа |
|---|---|---|
| BPM | 40–240 | `DSP BPM is outside musical range` |
| Key | Один из 12 chromatic keys | `DSP key is invalid` |
| Duration / RMS | Duration > 0 и RMS ≥ `1e-5` | `DSP audio metrics are invalid` |
| Полнота | Все обязательные поля приводимы к числу | `DSP features are incomplete` |

## Доказательства

Регрессии покрывают полностью валидный metadata payload, BPM=0, недопустимый key и silent RMS. Приёмка завершилась: `pytest tests/` — **85 passed**, `compileall` — успешно, AST-аудит — **0**.

> DSP extractor может вернуть BPM=0 для неритмического reference-аудио, например чистого тона. После ШАГА 036 такой результат честно отклоняется и не превращается в ложную музыкальную метрику.

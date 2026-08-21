# PLAN_v39 — ШАГ 048: matchering + loudness normalization

## Final mastering contract

`master_with_matchering()` теперь не принимает matchering output только по наличию файла. После matchering выполняется `normalize_master_loudness()` без добавления нового stylistic DSP: integrated loudness нормализуется к **−14 LUFS** при доступном `pyloudnorm`, а затем применяется ceiling. Fallback `mastering_pro` проходит тот же final normalizer, поэтому целевой level и ceiling не зависят от выбранного engine.

| Показатель | Реализация |
|---|---|
| Loudness | Target `−14 LUFS`; при отсутствии `pyloudnorm` используется явно маркированный `rms_approximation`, а не ложное утверждение LUFS measurement. |
| Peak safety | Normalizer применяет −1.2 dB sample headroom; `stage_master` проверяет 4× estimated true peak `≤ −1.0 dBTP`. |
| Duration/channels | Existing master quality gate проверяет ratio 0.95–1.05 и stereo output. |
| Evidence payload | Result включает `loudness`: target, mode, output LUFS если измерим, RMS dBFS, peak dB, sample rate и channels. |

## Evidence

Fake matchering теперь производит реальный stereo WAV, который проходит пост-нормализацию; regression проверяет `target_lufs=-14` и peak не выше −1 dB. На момент приёмки: `pytest tests/test_ai_quality.py tests/test_mastering_results.py -q` — **39 passed**; полный `pytest tests/ -q` — **116 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**.

> `matchering` и `pyloudnorm` не установлены в sandbox. Matchering/pyloudnorm inference и integrated-LUFS measurement честно **BLOCKED**. Real WAV adapter, RMS approximation path, ceiling, stage gate и contract tests проверены локально.

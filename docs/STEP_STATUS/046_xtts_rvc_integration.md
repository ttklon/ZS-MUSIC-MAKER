# PLAN_v39 — ШАГ 046: voice_synth_ai + RVC conversion

## Corrected runtime contract

`modules.voice_synth_ai.synth_vocal_ai()` теперь работает с фактическим public API: XTTS вызывает `tts_to_file`, а RVC вызывает `rvc_manager.infer(input_wav, voice_name, pitch_shift, out_name)`. Прежняя попытка вызвать несуществующий `handle.convert(input_path, output_path, model_path)` заменена; она не могла применить RVC через зарегистрированный `rvc_manager` handle.

| Этап | Поведение |
|---|---|
| XTTS | Может использовать уже загруженный `tts_handle` runner либо standalone registry lifecycle. Speaker WAV передаётся только если путь существует. Output обязан пройти `validate_vocal_artifact`. |
| RVC | Применяется только при явном `rvc_voice_name`/совместимом имени модели и доступном `rvc_handle`. Output переносится в project path и проверяется `validate_rvc_artifact`. |
| Provenance | Путь `rvc_model` сохраняется как provenance. Сам по себе произвольный `.pth` path не объявляется применённым: actual `rvc_manager.infer` адресует user-trained model по voice name. |
| Status | Успешная конверсия задаёт `rvc_applied=True`; отсутствие модели/runtime возвращает `rvc_skipped`, не выдавая fallback за voice conversion. |
| Orchestrator | `stage_vocal` подключён к `voice_synth_ai` с переданным XTTS handle. `stage_rvc` остаётся отдельной последовательной стадией и использует тот же public infer/quality contract. |

## Quality additions

`audio_metrics()` теперь сообщает `dc_offset`. RVC output отклоняется при offset выше **0.02**, помимо существующих проверок readable/signal/duration ratio 0.85–1.15. Это предотвращает принятие смещённого DC audio даже при формально корректной длительности.

## Evidence

Fake XTTS→RVC integration проверяет public `infer` parameters, `rvc_applied=True`, voice name, pitch shift и существующий project output. Отдельная WAV regression проверяет отказ DC offset. На момент приёмки: `pytest tests/test_ai_quality.py -q` — **37 passed**; `pytest tests/ -q` — **115 passed**; AI dry-run, `compileall` — успешно; AST-аудит — **0 dead imports**.

> Coqui TTS, `rvc-python`, user RVC model and GPU dependencies отсутствуют в sandbox. Real XTTS/RVC inference остаётся **BLOCKED**; adapter/public-API/quality contracts проверены с fake handles и реальными WAV artifacts.

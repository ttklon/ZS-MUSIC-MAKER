# PLAN_v39 — ШАГ 055: унификация Phonk engine

Обнаружен реальный incompatibility defect: `PhonkEngineV2` вызывал `generate_cowbell(frequency, duration_sec=...)`, а legacy `phonk_engine.generate_cowbell` принимал только `(notes, bpm, out_path)`. Canonical primitive теперь находится в `modules.phonk_engine`: modern API возвращает in-memory `float32` waveform для v2 composition, а legacy callers с `out_path` по-прежнему получают записанный WAV path.

Это сохраняет `PhonkEngineV2` как advanced composition layer (808 glide, plugins, musical intelligence) и переводит v1 на adapter-совместимость вместо конкурирующей реализации. Добавлены tests waveform duration/peak и legacy file-output contract.

На момент приёмки: `pytest tests/test_phonk_engine.py -q` — **2 passed**; полный `pytest tests/ -q` — **121 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**.

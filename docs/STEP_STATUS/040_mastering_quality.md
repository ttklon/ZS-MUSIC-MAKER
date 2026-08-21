# PLAN_v39 — ШАГ 040: quality gate mastering_ai

## Quality contract

`validate_master_artifact(input_path, output_path)` отсекает мастеринг до передачи в тегирование и экспорт. Проверка сначала подтверждает, что output действительно является воспроизводимым аудиофайлом, после чего сравнивает его с mix-источником. `true_peak_dbtp` вычисляется как **4× oversampled оценка** через `scipy.signal.resample_poly`; это измерительная оценка межсэмплового peak, а не декларация сертифицированного измерения аппаратным true-peak meter.

| Показатель | Допустимый диапазон | Причина отказа |
|---|---:|---|
| Каналы | Ровно 2 | `master is not stereo` |
| Длительность относительно mix | 0.95–1.05× | `master duration diverges from mix` |
| Estimated true peak | ≤ −0.5 dBTP | `master true peak exceeds ceiling` |
| RMS | −20.0…−5.0 dBFS | `master RMS is outside target range` |
| Файл и базовый audio signal | Не пустой, читаемый, не silent | Причина базовой `validate_audio_artifact` |

## Pipeline behavior

`stage_master` теперь добавляет `quality` к успешному ответу `master_ai` и заменяет `ok` результатом gate. Таким образом, matchering либо `mastering_pro` fallback не может быть принят только по факту отсутствия исключения: непригодный, mono, слишком тихий/громкий или укороченный файл возвращает `ok=False` и конкретную `reason`.

## Доказательства

Добавлены WAV-регрессии с реальными samples: валидный stereo-master и отдельные случаи true peak выше потолка, mono output, изменение длительности, RMS вне диапазона и отсутствующий output. На момент приёмки: `pytest tests/test_ai_quality.py -q` — **30 passed**; `pytest tests/ -q` — **96 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**.

> Реальный inference matchering остаётся **BLOCKED** из-за отсутствия зависимости в sandbox. Quality gate выполняется на реальных WAV независимо от выбранного mastering engine.

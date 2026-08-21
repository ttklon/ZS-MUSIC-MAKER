# PLAN_v39 — ШАГ 032: метрики, fallback и валидация faster-whisper ASR

## Quality contract

Перед сохранением ASR transcript вызывается `validate_asr_transcript()`. Валидатор измеряет число символов, токенов, уникальных токенов и их отношение. Он отсекает пустые/слишком короткие результаты и повторяющиеся петли из одного токена.

| Проверка | Реакция |
|---|---|
| Transcript содержит содержательный текст | Сохраняется в UTF-8 и возвращается `ok=True`. |
| Текст пуст, слишком короток или нет токенов | `ASR transcript is empty or too short`. |
| В тексте от 4 токенов, а unique ratio ≤ 0.25 | `ASR transcript is excessively repetitive`. |
| Transcript отклонён | Файл не записывается; возвращается `fallback: reference audio retained; transcript is not used`. |
| ASR runtime недоступен | Explicit `skipped: asr unavailable`; поддельный текст не создаётся. |

## Доказательства

Тесты покрывают нормальный русскоязычный transcript, пустой текст, зацикленный текст и integration-сценарий, где невалидный transcript не создаёт файл в dossier. На момент приёмки: `pytest tests/` — **80 passed**, `compileall` — успешно, AST-аудит — **0**.

> ASR model/weights отсутствуют в sandbox. Поэтому quality и fallback-контракты подтверждены, но реальная транскрипция large-v3 не заявляется как выполненная.

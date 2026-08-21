# PLAN_v39 — ШАГ 028: метрики, fallback и валидация RVC v2

## Quality contract

`validate_rvc_artifact(input_path, output_path)` проверяет два независимых условия: output должен пройти базовый audio gate, а его длительность должна оставаться в пределах 85–115% от исходного вокала. Такой допуск допускает техническую обработку, но блокирует обрывки, ошибочные короткие рендеры и несвязанные аудиофайлы.

| Проверка | Результат при нарушении |
|---|---|
| Исходный вокал читаем | `RVC input audio is unreadable` |
| Output читаем, не silent, без клиппинга | Причина общего audio gate |
| Output длится 85–115% от input | `RVC output duration diverges from input` |
| Нет модели/runtime | Explicit `skipped` из ШАГА 027; не применяется pitch-shift fallback. |

## Доказательства

Регрессия создаёт 1-секундный исходный вокал, корректный 1-секундный RVC output и 0.5-секундный output. Первый проходит, второй отклоняется с диагностикой длительности. На момент приёмки: `pytest tests/` — **73 passed**, `compileall` — успешно, AST-аудит — **0**.

> RVC model и runtime отсутствуют в sandbox. Quality gate проверен на аудиоконтракте и не служит доказательством реального timbre conversion.

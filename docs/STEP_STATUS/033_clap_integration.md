# PLAN_v39 — ШАГ 033: интеграция CLAP audio_tagger

## Реализованный контракт

Роль `audio_tagger` уже зарегистрирована как CLAP и поддерживается общим Hugging Face pull-маршрутом. Dossier-стадия теперь явно обрабатывает отсутствие bundle и использует `rank_clap_tags()` для преобразования `logits_per_audio` в tags из фиксированного словаря кандидатов.

| Сценарий | Поведение |
|---|---|
| CLAP bundle `(model, processor)` доступен | Аудио подаётся в processor, logits ранжируются в top-6 tags. |
| Модель на CUDA | Входные tensor-значения переносятся на CUDA. |
| CLAP unavailable | Возвращается `skipped: audio_tagger unavailable`. |
| Длина logits не совпадает со словарём | Поднимается явная ошибка контракта; неверная разметка не создаётся. |
| Runtime exception | Возвращается `ok=False` с диагностикой. |

## Доказательства

Тесты подтверждают сортировку top-N по score и отказ при несовместимых размерах scores/vocabulary. На момент приёмки: `pytest tests/` — **82 passed**, `compileall` — успешно, AST-аудит — **0**.

> CLAP/transformers weights отсутствуют в sandbox. Поэтому реальное автотегирование не заявляется как выполненное; registry/pull, bundle-контракт, ranking и безопасные отказные пути проверены отдельно.

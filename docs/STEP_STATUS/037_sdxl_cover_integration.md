# PLAN_v39 — ШАГ 037: интеграция SDXL cover_art

## Исправленный контракт

`stage_cover` ранее игнорировала переданный handle и вызывала renderer, который мог загрузить `cover_art` через registry повторно. Теперь переданный SDXL pipeline передаётся в `render_cover_ai(handle=...)`, а `render_cover_with_pipeline()` выполняет сам рендер. Тем самым lifecycle модели остаётся под контролем `SequentialAIRunner`.

| Сценарий | Поведение |
|---|---|
| SDXL handle доступен | Handle вызывается с prompt, 30 steps, guidance 7.0 и целевым размером; PNG сохраняется. |
| SDXL pipeline выбрасывает исключение | Возвращается `ok=False` с `SDXL cover generation failed`. |
| Модель unavailable | Existing optional fallback остаётся в `render_cover_ai`: генератор PIL используется только с явным `engine=PIL_fallback`. |
| Legacy caller без handle | Сохраняет совместимый путь `registry.use("cover_art")`. |

## Доказательства

Fake SDXL pipeline подтвердил прямой вызов handle, передачу size и создание PNG. Failing pipeline подтвердил прозрачную диагностику без ложного cover-успеха. На момент приёмки: `pytest tests/` — **87 passed**, `compileall` — успешно, AST-аудит — **0**.

> `diffusers`/SDXL weights отсутствуют в sandbox. Поэтому реальная диффузионная генерация не заявляется как выполненная; lifecycle и output-контракт проверены на совместимом handle.

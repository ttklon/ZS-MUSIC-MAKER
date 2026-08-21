# PLAN_v39 — ШАГ 034: метрики, fallback и валидация CLAP audio_tagger

## Quality contract

После ранжирования logits вызывается `validate_audio_tags()`. Набор tags должен быть непустым, не превышать top-6, не содержать повторов и полностью принадлежать исходному vocabulary CLAP stage. При нарушении tags очищаются до пустого списка и не передаются LLM-досье как достоверные признаки.

| Проверка | Реакция |
|---|---|
| Непустой набор не более 6 tags | Допускается к dossier. |
| Есть повтор | `audio tag output contains duplicates`. |
| Есть label вне vocabulary | `audio tag output contains unknown labels`. |
| Набор пуст или не является list/tuple | `audio tag output is empty`. |
| CLAP unavailable | Explicit `skipped`; fallback сохраняет reference audio без фиктивных tags. |

## Доказательства

Регрессии подтверждают прохождение уникального subset, отклонение duplicate labels и отклонение неизвестного label. На момент приёмки: `pytest tests/` — **83 passed**, `compileall` — успешно, AST-аудит — **0**.

> CLAP runtime/weights отсутствуют в sandbox. Продакшн-контракт качества подтверждён на output structure, но реальные classifier scores не заявляются как полученные на данном окружении.

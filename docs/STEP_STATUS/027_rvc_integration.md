# PLAN_v39 — ШАГ 027: интеграция RVC v2

## Исправленный контракт

AI-оркестратор ранее пытался вызвать у RVC handle метод `convert`, которого в публичном `modules.rvc_manager` нет. Интеграция приведена к реальному API `rvc_manager.infer(input_wav, voice_name, pitch_shift, out_name)`.

| Условие | Поведение |
|---|---|
| RVC runtime и user model доступны | Вызывается `infer`, результат копируется в `<project>/vocal_rvc.wav`. |
| Пользователь не передал имя голоса | Стадия возвращает `skipped: no rvc_voice_name`. |
| Нет RVC runtime/model | Стадия возвращает явный `skipped: RVC unavailable`. |
| `infer` падает или не создаёт файл | Возвращается `ok=False` с диагностикой. |
| Возникает желание применить pitch-shift вместо RVC | Не применяется: такой fallback прямо запрещён существующим `rvc_manager`. |

## Доказательства

Контрактный тест fake RVC manager подтверждает точную передачу `input_wav`, `voice_name`, `pitch_shift` и копирование полученного WAV в project output. Отдельный тест runtime-ошибки подтверждает честный failure без подмены. На момент приёмки: `pytest tests/` — **72 passed**, `compileall` — успешно, AST-аудит — **0**.

> В sandbox нет user-supplied `.pth` и `rvc-python`. Поэтому реальная voice conversion не заявляется как выполненная; интеграционный путь и безопасный отказ проверены отдельно.

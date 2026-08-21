# PLAN_v39 — ШАГ 039: интеграция mastering_ai (matchering)

## Реализованный контракт

`modules.mastering_ai.master_with_matchering()` принимает **уже загруженный** handle роли `mastering_ai`, исходный mix, reference и путь назначения. Адаптер вызывает API matchering `process(target=..., reference=..., results=[pcm16(...)])`, а затем подтверждает физическое создание выходного файла. Пустой успешный ответ без артефакта считается ошибкой, а не готовым мастерингом.

`stage_master` в `app/core/orchestrator_ai.py` теперь получает handle от последовательного runner и передаёт его в `master_ai(..., handle=handle)`. При наличии `reference_master_wav` стадия объявляется role-backed (`mastering_ai`); lifecycle загрузки/выгрузки остаётся у runner. При отсутствии reference роль не загружается и используется существующий честный DSP fallback `mastering_pro` с причиной `no reference`.

| Сценарий | Результат |
|---|---|
| Есть reference и runner передал handle | Выполняется matchering через переданный handle; вложенный `registry.use()` отсутствует. |
| Matchering завершился без файла или выбросил исключение | Ошибка фиксируется как `fallback_reason`, затем выполняется `mastering_pro`. |
| Reference отсутствует | Модель не загружается; запускается `mastering_pro`, `fallback_reason=no reference`. |
| Вызов `master_ai` вне runner с доступной ролью | Сохраняется обратная совместимость: допустима локальная `registry.use()` загрузка. |

## Доказательства

Добавлены два детерминированных теста с fake-handle: проверка параметров `target`/`reference` и проверка отказа при отсутствии созданного выходного файла. На момент приёмки: `pytest tests/test_ai_quality.py -q` — **24 passed**; `pytest tests/ -q` — **90 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**.

> `matchering` не установлен в sandbox, поэтому фактический inference не заявляется выполненным. Реально проверены независимый adapter-контракт, передача handle из runner и fallback-поведение без тяжёлой зависимости.

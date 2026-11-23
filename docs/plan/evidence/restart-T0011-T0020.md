# Повторная приёмка T0011–T0020 — контракт результата

Принимается типизированный контракт и запрет ложного успеха. Создание или
качество настоящей автоматически спетой песни этим пакетом не объявляются
реализованными: текущие producer не выдают принятых content manifests.

| ID | Работа и предметная проверка |
|---|---|
| T0011 | Повторно закреплены четыре разных типа, unverified_audio, явный запрос caller и различие технического success / качества. Документ RESULT_CONTRACT обновлён. |
| T0012 | Реально исполнен прежний result.py из HEAD d3909d4 над PCM-фикстурой с валидным manifest: failed outcome, dry_run и voice.ok=false давали succeeded=true. После исправления все три false. Checkout/смена ветки не использовались. |
| T0013 | Происхождение не может отменять отказ исполнения; request принадлежит caller, не producer. Никакого распознавания пения по синусоиде или добавления фиктивных checks=true в production. |
| T0014 | assess_result отвергает отказы, отмену, QA, partial/only, synthetic/placeholder, явный пустой/речевой вокал; типы schema/engine/revision и явный invalid manifest проверяются строго. |
| T0015 | Agent CLI явно требует generated_singing и возвращает nonzero на downgrade; malformed producer завершает NDJSON done ok=false. UI сверяет request/kind, valid artifact/path/hash, reasons/blocked и task outcome. |
| T0016 | Отрицательные случаи включают тишину, битый/NaN/Inf WAV, stale hash, TTS/RVC без подтверждения singing, явные empty/silent и lyrics failure, неверные типы и противоречивый outcome. Намеренный instrumental не требует вокал. |
| T0017 | Локально 99 Python tests (result/agent/transport/budgets) и 38 JS creation/UI прошли. Проверяются и положительные все четыре типа с fixture provenance, и отрицательные случаи. Это не модельные renders. |
| T0018 | Windows workflow выполняет реальные PCM проверки и Node/UI regression; --window-check дополнительно исполняет typed result fixtures в настоящем renderer, без запуска backend/загрузок. Результат ниже после job. |
| T0019 | Критерий: старые три ложных успеха устранены; речь, invalid artifact и чужой requested kind не проходят UI, CLI отдаёт nonzero. Положительный технический контракт остаётся возможным, quality_accepted=false. |
| T0020 | RESULT_CONTRACT, workflow path filters и регрессии обновлены; ограничения producer trust и отсутствие независимого прослушивания сохранены. Приёмка требует Windows evidence, а не наличия файлов. |

## Команды

```sh
python -m pytest tests/test_result_acceptance_contract.py tests/test_agent_guide.py tests/test_recipe_transport.py tests/test_function_length_budget.py -q
node --test desktop/test/creation.test.js desktop/test/ui-contract.test.js
```

Baseline был воспроизведён через git show HEAD:app/pipeline/result.py и exec
доверенного содержимого в отдельном namespace. Для трёх случаев observed before
succeeded=true, observed after succeeded=false; master — stdlib WAV-файл с синусом
0.3 секунды, не вокал и не музыка. Он проверяет провод и классификацию.

Все изменения остаются в текущей ветке; версия приложения не повышается,
установщик не публикуется. Данные пользователя не удаляются. Прежние результаты
проверок других пакетов не копируются автоматически в complete.

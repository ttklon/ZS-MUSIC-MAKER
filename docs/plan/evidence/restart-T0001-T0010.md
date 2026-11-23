# Повторная предметная приёмка T0001–T0010

Объём: единая спецификация поддерживаемого продукта и её согласованность с
метаданными поставки, README, PRODUCT и настоящей упакованной справкой.
Это НЕ приёмка генерации, пения, GPU или пользовательского пути всего продукта.
Предыдущая работа над T0011–T0050 сохранена, но не засчитана автоматически.

| ID | Выполненная работа и предметная проверка |
|---|---|
| T0001 | Повторно сверены schema 1, Windows 11 x64, Electron, per-user NSIS, четыре обязательных сценария и их ограничения. Добавлен общий строгий validator структуры. |
| T0002 | Реально выполнен `git show 39f8a85:desktop/src/sections/help.js`: строки 41 и 46 воспроизводят старые ложные заявления об отсутствии Python-кода и сети. Текущая справка их не содержит. |
| T0003 | Один источник product-contract.js сохранён; validator используется Node metadata check и browser help. Отдельная декларация возможностей не создана; packaged verifier сверяет видимое содержимое. |
| T0004 | Исправлен допуск пустых/повторных сценариев, неверных accepted/required, пустой причины и отсутствующего обязательного текста. Invalid contract теперь отвергается до metadata check. |
| T0005 | Справка рендерит отдельный product-scenarios, использует общую валидацию; Windows probe проверяет все видимые поля и четыре сценария, а не только product ID. |
| T0006 | Негативные тесты: повреждённый контракт, пустой список, дубли, неверный флаг, пропущенная причина и некорректный versionSource; UI даёт восстанавливаемую ошибку. Проекты/веса не затрагиваются. |
| T0007 | Product/render/UI regression: 46 passed. Проверка очереди/плана/бюджета функций: 16 passed. Positive/negative packaged-text verifier отдельно отвергает правильный ID с отсутствующим текстом. |
| T0008 | Новый Windows job specification-first-ten запускает реальный упакованный EXE и требует productHelpVerified=true. Результат записывается ниже после job. |
| T0009 | Критерий: metadata и generated docs совпадают, настоящий renderer показывает канонические тексты/границы всех четырёх сценариев. До Windows результат не засчитывается автоматически. |
| T0010 | Обновлены desktop/README, PROJECT_STATE и EXECUTION: новый проход по 10, история не принимается за текущую очередь. restart validator и negative tests запрещают пропуски и закрытие без приёмки. |

## Воспроизведение

```sh
node desktop/scripts/product-spec.js --check
node --test desktop/test/product-contract.test.js desktop/test/render.test.js desktop/test/ui-contract.test.js
python -m pytest tests/test_plan_restart.py tests/test_product_plan.py tests/test_function_length_budget.py -q
python tools/check_plan_restart.py
```

Все сценарии продукта остаются accepted=false. Сборка в CI предварительная,
без публикации, тега, изменения runtime версии и удаления release assets.
Откат: revert соответствующих исходников и документов; данные пользователя не
удаляются. Генератор плана поверх статусов не запускался.

# T0021–T0030: проверка остатка против исходного плана

Основание: docs/plan/PLAN_1000.md, пакет 003. Эта запись исправляет
слишком общий remaining, а не меняет критерии и не принимает пакет.

## Почему работа затянулась

После настоящего CPU pipeline результата работа ушла в серию дополнительных
проверок отдельного JS-раздела «Бит». GUI clicks/cancel, memory и input checks
реальны, но не закрывают центральный остаток измеренных CPU/GPU профилей и
интеграции hardware-контракта с установленным приложением/общим рецептом.
Одинаковый remaining у восьми разных ID скрывал эту разницу.

| ID | Уже имеется | Конкретный недостающий результат |
|---|---|---|
| T0021 | Inventory/resource/inference разделены; fail-closed контракт и Windows CPU отчёты | Свести именно заявляемые конфигурации с протоколами и точными пределами; не назвать CUDA/AMD поддержанными без inference |
| T0022 | Воспроизведены malformed budget, unknown RAM/VRAM, missing execution, false-success | Baseline существует; отдельного нового GUI-сценария здесь не нужно. Общий предметный критерий пакета ещё не принят |
| T0023 | Канонические hardware/registry guards; измерения отдельно от оценок | Явно зафиксировать альтернативы/rollback для hardware-интеграции установленного продукта, не для JS beat |
| T0024 | HardwareBudget/checked_gib/RAM/VRAM reserve, реальный CPU producer trace | Полная матрица измеренных заявляемых CPU/GPU конфигураций отсутствует; оценки не заменяют её |
| T0025 | Python adapter/result и packaged renderer, отдельно JS GUI click | Настоящий путь установленное приложение → общий рецепт → hardware preflight → Python pipeline, с результатом или обоснованным отказом |
| T0026 | RAM deny/retry, source/hash/outcome negatives; JS GUI cancel/retry | Отказ hardware preflight и повтор через тот же installed/shared-recipe путь; JS cancel не выдавать за отмену всех model workers |
| T0027 | Windows contract suite + реальные CPU probes; doubles обозначены | Регрессия недостающей installed hardware-интеграции после реализации T0025/T0026 |
| T0028 | Windows jobs и durable CPU/GUI reports | Installed/shared-recipe протокол; реальные CUDA/AMD trials отдельно остаются непроведёнными |
| T0029 | CPU speech, procedural music, hashes/time/RAM; GPU не сертифицирован | Реальные модельные/полные заявляемые CPU/CUDA/AMD профили: версии, входы, backend, время/RAM/VRAM и исход; не JS GUI тест вместо них |
| T0030 | Документы и evidence сохранены | Закрытие после T0029; согласованная матрица поддержки, без открытого остатка |

## Следующий фокус, без расширения побочных тестов

1. Проверить канонический installed recipe/preflight путь T0025 и его фактические
   точки интеграции; исправлять обнаруженный разрыв, а не строить ещё один renderer.
2. Довести его hardware deny/retry протокол T0026–T0028 на Windows.
3. Получить реальные CUDA/AMD измерения T0029. Наличие доступного GPU runner
   пока **не установлено**: запрос GitHub runners API вернул HTTP 403
   Resource not accessible by integration. Это ограничение API, не доказательство
   отсутствия GPU и не результат GPU-теста. CPU hosted run не подменяет его.
4. Полное принятие только по исходному критерию. Не понижать требования,
   не пропускать IDs и не переводить счётчик ради видимого прогресса.

NSIS/пение/quality относятся к конкретному заявляемому продуктовому пути:
не делать из каждого глобального требования новый несвязанный мини-проект
внутри каждого hardware ID. Но установленный путь прямо требуется T0025.

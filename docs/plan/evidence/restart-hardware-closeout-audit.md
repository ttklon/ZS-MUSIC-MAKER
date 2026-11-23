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

## Windows installed-path acceptance update — 2026-11-23

[Run 45207868772](https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45207868772),
source `405cd6bd52ea070b4a51decf09d5f39f3891ed98`: все три jobs прошли,
включая `Clean NSIS install, actual installed window, ACL and uninstall`.
Сохранённый summary и ссылка на `nsis-install-check` artifact:
`restart-hardware-installed-path-windows-45207868772.json`.

- T0025/T0027/T0028 закрыты в повторной приёмке: установленный current-creation
  UI → agent-hit IPC → общий task runner → bundled Python, regression и Windows
  NSIS path прошли.
- T0026: отказные RAM/disk/VRAM сценарии, незабюджетированный MusicGen, отсутствие
  записи при отказе, сохранность файла и measured retry проверены этим путём.
  T0026 остаётся открытым: реальная отмена model-worker tree не проверена; GUI
  cancel не считается доказательством такой отмены.
- Bootstrap fixture только разблокирует кнопку; setup/install acceptance не
  заявляется. Низкие/неизвестные ресурсы для deny cases синтетические. Retry
  использует измеренную Windows-инвентаризацию и procedural DSP; inference,
  product profile, качество песни и CUDA/AMD не приняты.
- A0003/A0004 получили technical pass в отчёте CI, но формальная приёмка ожидает
  независимого owner; G0–G9 не менялись.

## Следующий фокус, без расширения побочных тестов

1. Закрыть оставшееся у T0026: наблюдаемая отмена дерева model workers, не только
   UI-задачи; сохранить доказательство на Windows.
2. Довести T0021/T0024/T0029: реальные полные измерения именно заявляемых
   CPU/CUDA/AMD профилей — версия, вход, выбранный backend, время, RAM/VRAM и
   исход; не считать процедурный DSP или оценку памяти модельным inference.
3. Наличие доступного GPU runner всё ещё **не установлено**: предыдущий запрос
   GitHub runners API вернул HTTP 403 `Resource not accessible by integration`.
   Это ограничение API, не доказательство отсутствия GPU; hosted CPU runner его
   не подменяет.
4. T0030 закрывать только после измеренной матрицы и согласованного списка
   поддерживаемых профилей. Не понижать критерии и не переводить счётчик ради
   видимого прогресса.

NSIS/пение/quality относятся к конкретному заявляемому продуктовому пути:
не делать из каждого глобального требования новый несвязанный мини-проект
внутри каждого hardware ID. Но установленный путь прямо требовался T0025.

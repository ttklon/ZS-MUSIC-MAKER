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
| T0026 | Installed RAM/disk/VRAM deny + retry/file preservation; UI Stop kills the real SequentialAIRunner stage-worker process and releases its lock (test-only model=None) | Отказ hardware preflight и recovery проходят установленный shared-runner путь; lifecycle test не является model loading/inference или GPU acceptance |
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

## T0026 follow-up — installed stage-worker cancellation, 2026-11-23

[Run 45217099122](https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45217099122),
source `089d819053fe7552d5477d815345f1594b87334c`: clean installed Windows check
прошёл. Текущий creation UI остановил agent-hit, пока тот исполнял test-only stage
в реальном изолированном `SequentialAIRunner` worker; проверены подтверждённое
termination, исчезновение worker/task процессов и повторное получение файлового
lock. Гейт запуска считает `modelWorkerCancellation` обязательным для
`agentPreflight.ok`, поэтому зелёный NSIS step означает, что все эти assertions
прошли. Подробный payload артефакта не скачан (artifact ID `14838169314`, redirect
на недоступный sandbox egress host); точные ephemeral PIDs не архивированы.

T0026 в строгой restart-переоценке закрыт; backlog status остаётся `verified` и
не изменён. Cancellation fixture задаёт `model=None`: это доказывает lifecycle
реального stage-worker процесса, не model loading/inference, GPU или качество.
Независимый owner для формальной A0003/A0004 приёмки по-прежнему не назначен.

## Следующий фокус, без расширения побочных тестов

1. Довести T0021/T0024/T0029: реальные полные измерения именно заявляемых
   CPU/CUDA/AMD профилей — версия, вход, выбранный backend, время, RAM/VRAM и
   исход; не считать procedural DSP или оценку памяти модельным inference.
2. Доступный Windows CPU runner **подтверждён** успешным [run 45166373798](https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45166373798): реальный Silero v3_1_ru CPU inference, подробности в `restart-hardware-strict-windows-45166373798.json`. Это узкая речь, не полный музыкальный профиль; runner был на другой ветке/commit, а не на текущем HEAD. Попытка запустить workflow на активной ветке вернула HTTP 403 `Resource not accessible by integration`; rerun старого workflow GitHub также отклонил.
   Доступность **GPU** runner по-прежнему не установлена: предыдущий GitHub runners API-запрос дал HTTP 403, что не доказывает отсутствие GPU. Инвентарь временной Arena Linux VM (`restart-hardware-sandbox-inventory-20261123.json`) не увидел GPU только в этой VM и не заменяет проверку других runners.
3. T0030 закрывать только после измеренной матрицы и согласованного списка
   поддерживаемых профилей. Не понижать критерии и не переводить счётчик ради
   видимого прогресса.

NSIS/пение/quality относятся к конкретному заявляемому продуктовому пути:
не делать из каждого глобального требования новый несвязанный мини-проект
внутри каждого hardware ID. Но установленный путь прямо требовался T0025.

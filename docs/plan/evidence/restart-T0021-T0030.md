# Повторный проход T0021–T0030 — работа продолжается

Код: c5117db3d4398fd7597c5f0abb210b4bb32b73f4.
Windows inference: https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45141041526
(запущен; результат при создании записи ещё не получен).

- T0021: контракт ресурсов и границ доказательств описан в docs/HARDWARE.md.
- T0022: воспроизводимые негативные случаи: NaN/Infinity/отрицательная оценка,
  bool/строка, нулевая свободная VRAM при нулевой оценке.
- T0023: fail-closed проверки, фактическая свободная VRAM плюс резерв; отдельно
  инвентарь, разрешение ресурсов и измеренный inference.
- T0024: checked_gib, HardwareBudget validation, RAM guards и VRAM reserve.
- T0025: проверки подключены к существующим ModelRegistry и ASR/LLM guards.
- T0026–T0028: локальный набор hardware/registry/Silero/benchmark/length:
  74 passed. Это контрактные тесты, не inference и не тесты всех GPU.
- T0029–T0030: полная приёмка НЕ заявлена. Запущен новый настоящий Windows
  Silero CPU benchmark; CUDA/AMD inference этим запуском не проверяются.

Дополнительно upstream Silero loader закреплён commit SHA; модельный пакет
хешируется в benchmark, но его digest ещё не является allowlist доверенных весов.
Python socket guard не заменяет независимый OS-level сетевой аудит.
Пакет из десяти пунктов остаётся активным, счётчик принятых не увеличен.

## Продолжение: измерения и Windows-регрессия

- 45141041526: весь workflow failed. Есть notice успешных аудиопроверок,
  но это не равнозначно успешному job. Прямая загрузка логов недоступна в
  sandbox. Публикация JSON сделана ASCII-safe; регрессия воспроизводит
  печать русских полей через строгую cp1252 без исключения.
- 45142874352: **real-silero job 137584922710 success**, source
  57907020318c2ed7d8bc95f898d77df90df3cbbf. Отчёт из GitHub annotations
  сохранён в `restart-hardware-silero-45142874352.json`.
  Online: аудио 3.875 s, wall 12.5343 s, sampled RSS 773193728 bytes.
  Offline: аудио 4.6875 s, wall 8.9905 s, sampled RSS 990769152 bytes,
  RTF 1.918, Python network attempts 0. Torch 2.5.1+cpu, RAM 15.99 GiB.
  Это реальная черновая речь, не музыкальный inference/пение.
- Workflow 45142874352 всё ещё failed из-за PowerShell: ожидаемый отказ pip
  оставлял LASTEXITCODE=1. Добавлен exit 0 **только после проверки** точного
  конфликта AudioCraft/Torch. Не маскируются произвольные ошибки сети/pip.
  Установка AudioCraft этим тестом не подтверждается.
- Инвентарь профиля теперь использует detect_system: адаптеры, PyTorch device,
  DirectML отдельно; mock AMD/DirectML остаётся явно непроверенным inference.
- 45143253532: Windows-контракт обнаружил зависимость теста от заранее
  установленной librosa (1 failed, 73 passed). Тест import-контракта исправлен:
  проверяет как подставленный модуль, так и отсутствие модуля. Продуктовая
  проверка зависимости не ослаблена.
- Добавлены retry после отказа RAM без изменения прежнего файла и совместимость
  задания только CPU_THREADS (автоматически ограничивает detected CPU_CORES).
- Финальный локальный набор: **115 passed** (hardware/registry/offline/benchmark,
  bootstrap/dependencies, plan/product, function budget).
- Финальный Windows-прогон **45143489947**, source
  201d933d39a6703fe8932af9a6da6cbf1914c6c7: **SUCCESS, оба job**.
  Hardware/offline/registry contracts: **76 passed on Windows**.
  Реальный offline Silero: 4.6875 s аудио / 6.2315 s wall, RTF 1.3294,
  sampled RSS 1049825280 bytes; Python network attempts 0.
  RAM 15.99 GiB, 4 потока/2 ядра; PyTorch GPU отсутствует.
  Полный JSON: `restart-hardware-windows-45143489947.json`.
  Зелёный resolver job означает проверку ожидаемого отказа несовместимых
  зависимостей и bootstrap guard, НЕ успешную установку AudioCraft.

Открытая предметная работа: реальные полные продуктовые сценарии, CUDA и AMD
на физически доступном оборудовании. Hosted CPU runner не подменяет их.

## Настоящий музыкальный CPU-render (продолжение)

Добавлен `tools/desktop_render_benchmark.js`: использует production
`desktop/electron/render-host.js` → настоящий worker → `pipeline.js`, без
подмены рендера. Вход: phonk / A minor / BPM 140 / seed 7 / 20 или 120 s,
`useBank=false`, вокал `none`: явно запрошенный процедурный инструментал,
НЕ нейронная генерация, пение или полный путь создания песни.

До замера выполняется настоящая отмена по progress и повтор. После рендера
проверяются RIFF/data length, PCM16 stereo 44100 Hz, точная длительность,
peak/RMS, SHA-256. Wall time включает worker startup/передачу WAV, не запись
на диск. maxRSS — lifetime всего Node-процесса с worker threads, отменой и
проверкой WAV, не отдельный GPU-пик и не минимум RAM для пользователя.

Локально Linux: 20 s / 7.0004 s wall / 261029888 bytes maxRSS;
120 s / 33.9766 s wall / 877973504 bytes maxRSS. Сеть этими тестами не
аудируется (`network_verified=false`). Локальные регрессии: 41 JS passed,
29 Python passed; тест summary отдельно 2 passed.

Windows 45145659002, source 209c0a4f5d42fc4980cd10c2ecdde2fb1701e1c1:
**SUCCESS все четыре job**, включая реальные 20 s и 120 s DSP renders,
Silero и bootstrap negative guard. Полный DSP JSON находится в artifacts;
GitHub annotation обрезала большой engine report, поэтому вместо попытки
выдать неполный JSON за доказательство добавлена компактная summary с
регрессией длины <3800 символов. Повторный прогон 45146015331 (source
6ebbfa4117976e97cdd3e331caef1c4b78c335f4): DSP **оба job success**,
bootstrap success, но Silero failed до inference с HTTP403 rate limit exceeded.
Этот workflow целиком не зелёный. Сохранённый протокол:
`restart-hardware-dsp-windows-45146015331.json`.

| Windows procedural workload | Wall s | Process lifetime maxRSS MiB | CPU runner |
|---|---:|---:|---|
| 20 s | 6.4104 | 267.5625 | Xeon Platinum 8370C, 4 logical CPUs |
| 120 s | 27.5845 | 852.0391 | AMD EPYC 7763, 4 logical CPUs |

Оба runner RAM ~16 GiB; это **разные CPU**, не сравнение масштабирования
на одной машине. Hash 20 s совпал с локальным Linux WAV. Это байтовая
воспроизводимость этого входа, не гарантия для всех движков/версий.

Silero Torch hub выполнял API discovery даже для закреплённой ревизии.
В 0df0f88 добавлен skip_validation=True только к константному reviewed SHA;
ветка/произвольный ref не принимаются как параметры. Это исключает branch/fork
API enumeration, но не сетевые ошибки скачивания. Отдельный digest пакета
по-прежнему записывается; это не allowlist доверенных весов.
Прогон после исправления: **45146340788 SUCCESS все четыре job**,
source 0df0f88f5d5c03a1001c47615ea7c2689567b4b9.
[Сохранённый JSON](restart-hardware-windows-45146340788.json).
Windows hardware contracts: 76 passed; DSP validation/cancel/retry: 2 passed
на каждом matrix runner (реальные workers).

| Финальный Windows procedural workload | Wall s | Process lifetime maxRSS bytes |
|---|---:|---:|
| 20 s (EPYC 7763 / 4 logical CPUs) | 5.8763 | 262434816 |
| 120 s (EPYC 9V45 / 4 logical CPUs) | 17.2189 | 895328256 |

Узкий CPU-инструментал измерен; полная песня/GPU-профили не сертифицированы.
Счётчик повторно принятых остаётся 20; следующий пакет не перескакиваем.

Попытка получить список self-hosted runners через GitHub API вернула HTTP403
`Resource not accessible by integration`. Это ограничение видимости, а не
доказательство отсутствия GPU runners. Доступного NVIDIA/AMD inference
этими прогонами не получено; статусы GPU не повышались.

## Строгий offline runner для конкретного backend

Код `bb528dad5e6f9e08c1993fb3c058a760623df568`:
`tools/local_model_benchmark.py`. Обязательны локальный доверенный пакет,
SHA-256 и явный backend cpu/cuda/rocm. Отказ при несовпадении хеша происходит
до исполняемой загрузки; недоступный backend не подменяется CPU. ROCm/HIP
не выдаётся за NVIDIA CUDA; DirectML не поддерживается этой пробой.
Выходной tensor должен находиться на запрошенном устройстве/index; для GPU
обязательна положительная peak allocated VRAM. Замер включает synchronize,
загрузку/transfer, inference, CPU conversion и запись WAV.
Это узкий backend probe речи, не полный музыкальный профиль и не трассировка
всех внутренних kernel модели. Никаких скачиваний модельных весов.

Негативная регрессия (doubles, не inference): CUDA unavailable, ROCm/CUDA
mismatch, DirectML rejection, неверный digest/отсутствующий пакет, неверный
output device/index, отсутствие вызова model loader при недоступном backend,
сохранение предыдущего WAV при отказе и report.ok=false.
Финальный локальный набор **124 passed**.

[Windows 45148490225](https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45148490225):
**SUCCESS все четыре job**; 85 hardware/offline/backend contract tests,
настоящие DSP 20/120 s и новая строгая offline Silero CPU-проба.
[Сохранённые отчёты](restart-hardware-strict-windows-45148490225.json).
Strict CPU: 5.775 s речи, wall 9.2548 s, sampled RSS 909131776 bytes,
RTF 1.6026, Python network attempts 0; модельный SHA
`cf60b47ec8a9c31046021d2d14b962ea56b8a5bf7061c98accaaaca428522f85`.
`inference_verified=true` относится только к этому реальному CPU-синтезу;
`product_profile_accepted=false` сохранён. Полный hardware inventory в artifact;
в сохранённой compact summary он исключён ради лимита GitHub annotation.

CUDA/ROCm ветки имеют только контрактные тесты с doubles; реальных GPU
измерений в этом изменении нет. Windows AMD GPU/DirectML не приравниваются
к ROCm или AMD CPU hosted runner. Полный путь песни не принят.
Пакет остаётся активным без увеличения счётчика выполненных пунктов.

## Classic Python orchestration: реальный мастер не равен полной приёмке

Код `f0ebf972a48432258f88276038f3f5c8bc024857`:
`tools/pipeline_hardware_probe.py`. Новый каталог обязателен, существующий
прогон не перезаписывается. CPU, procedural, voice off, streaming-only,
quality fast, stems off; пользовательский текст задан только как метаданные.
Все стадии вызываются production `run_full_pipeline`, `dry_run=False`,
без `only`, без подмены исполнителей. Python socket guard и offline policy;
CUDA_VISIBLE_DEVICES скрывает CUDA до импортов в отдельном CLI-процессе.
Это не OS sandbox, не ROCm/DirectML isolation и не GPU-профиль.

Локальный реальный результат: diagnostic master 20.0 s, wall 25.5687 s,
sampled RSS 371294208 bytes; outcome **blocked**, exit **1**. Запущенные
mix/master/QA/release стадии успешны, но есть обязательные blocked стадии:
MusicGen texture, voice off, stems off. Не меняли required contract и не
переклассифицировали этот результат в success ради зелёного benchmark.

[Windows 45149932663](https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45149932663):
**SUCCESS все пять job**. Classic diagnostic job проверяет **ожидаемый отказ**:
реальный probe exit 1, `ok=false`, `outcome_status=blocked`, настоящий
20.0 s polished.wav, wall 36.9244 s, sampled RSS 474902528 bytes. Отдельный
контроль требует OK у mix/master/auto_qa/release; отсутствие мастера/другая
ошибка не засчитываются как ожидаемая неполнота.
[Сохранённая compact summary и job metadata](restart-hardware-classic-windows-45149932663.json).
Зелёный job НЕ означает successful pipeline/product profile: он доказывает,
что имеющийся мастер не повысил неполный прогон до PASS. Полный report, WAV
и журналы находятся в workflow artifact `windows-classic-pipeline-diagnostic`.

Регрессия: 127 локальных Python tests passed (включая общий hardware/result
набор); отдельно 39 outcome/probe/function tests passed. Добавлены:
отказ от повторного использования каталога, наличие файла при failed outcome,
противоречивые succeeded/status, dry/partial, неверная длительность.
Наличие diagnostic_audio никогда не заменяет `ok=true`.

Открытая работа теперь подтверждена исполнением: classic full-success ещё не
получен, не только не измерен; CUDA/AMD GPU физически не испытаны. В повторном
проходе T0021–T0030 не закрыт и счётчик 20 не повышен.

## Явно ограниченный CPU-запрос: первый classic canonical success

Код `b14321da6ae05cefe787eb42077d1cfc74b4d323` исправляет false-negative
для явно отключённых caller-ом стадий. `not_requested_names` передаётся
нормализованным caller recipe, а не берётся из worker output. Только BLOCKED
может стать canonical `not_requested`; FAILED/CANCELED/UNKNOWN/FALLBACK не
скрываются. `required_names` имеет приоритет; пропавший обязательный master
остаётся blocked. Пустой обязательный scope не даёт success. Raw stage status
не переписывается в OK, явно отключённая стадия остаётся видимой в отчёте.

`use_texture` по умолчанию true; только литерал false отключает texture.
Таким образом недостающая запрошенная MusicGen остаётся блокером, а не
автоматически выключается по hardware. Voice off и stems false учитываются
как явные границы запроса. Частичный `only` и dry run всё ещё не success.
Generic `outcome_from_report` намеренно не доверяет producer request_scope и
не повышает результат на его основании: такая граница по умолчанию остаётся
консервативной. В этой итерации подтверждён direct classic Python API / probe,
не вся цепочка typed-result adapters и не установленный GUI.

В процессе настоящего запуска найден локальный ACE-Step discovery connect
на 127.0.0.1:8001. Не разрешали его через socket guard. Добавлен явный runtime
opt-out `ZSMM_PROBE_LOCAL_SERVICES=0` (default discovery вне probe сохранён).
Сокет закрывается context manager-ом и при ошибке. Probe задаёт opt-out перед
production импортами. Это конфигурация реального запуска, не mock функции.

[Windows 45151624994](https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45151624994):
**SUCCESS все пять job**, source b14321d. Реальные сценарии на одном classic
runner в отдельных Python-процессах:

| Запрос | Probe exit / outcome | Wall s | Sampled RSS bytes |
|---|---|---:|---:|
| texture requested (default), voice/stems off | 1 / blocked | 56.4760 | 466980864 |
| texture explicitly off, voice/stems off | 0 / success | 27.5456 | 356839424 |

В обоих случаях WAV 20.0 s, SHA
`ef1018be785fee33aadca425ae2adb47908ac643d9a8c55118f2ec3887ed45cf`:
одинаковый файл НЕ означает одинаковую полноту запроса. Это и проверяется.
[Сохранённые job metadata и summaries](restart-hardware-scope-windows-45151624994.json).
Подробные reports/WAV/request_scope — artifact windows-classic-pipeline-diagnostic.
Локальная регрессия: **191 passed** (outcomes, recipe/transport, vocal chain,
hardware/backend/offline, plan/product, function budgets).

Теперь получен canonical success ограниченного CPU-инструментального запроса.
Не получены full song/singing, универсальный CPU profile, CUDA/AMD GPU и полная
adapter/installed-GUI приёмка. T0021–T0030 остаётся активным; счётчик 20.

## Доверенный scope через адаптеры и typed result boundary

Source `b2fd280d3c571701da2378127d215ac9e04cc68b`:
`classic_execution_contract`, `classic_outcome`, `classic_result` в
`app/core/stage_request.py`. Новый caller-supplied contract явно передаётся
в outcome/result validators; default generic validator остаётся строгим и
не читает разрешения из report.request_scope/report.recipe.
God/async адаптеры фиксируют contract **до** вызова исполнителя: изменение
переданного state изнутри executor не может задним числом выключить стадии.

Дополнительно найден и закрыт bypass: при переданном caller required contract
producer мог не возвращать outcome/stages вообще. Теперь такая пустая
execution envelope проверяется на отсутствующие обязательные стадии даже
при существующем WAV и формально подходящем content manifest.
Scope не обходит missing master, FAILED/CANCELED, QA, dry/partial, привязку
content evidence к хешу и caller requested kind.

Тест async с фиктивными только beat/master раньше ожидал completed: исправлен
на partial/blocked, поскольку остальные caller-required стадии отсутствуют.
Отдельные позитивные doubles предоставляют весь stage contract, а не снижают
требования ради теста. Эти God/async тесты не являются model/GUI inference.
Локальная расширенная регрессия **285 passed**.

[Windows 45153740505](https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45153740505):
**SUCCESS все пять job**. [Сохранённые результаты](restart-hardware-adapters-windows-45153740505.json).
Настоящий classic CPU probe со scope, без texture:
20.0 s / 26.7133 s wall / sampled RSS 329687040 bytes,
producer outcome **success**, caller adapter **success**, typed result
**degraded**. Последнее ожидаемо: execution scope не подделывает недостающее
подтверждение состава аудио. Для этого прогона не изготовляли фиктивный
`music_present` manifest, чтобы насильно получить typed success.

С texture requested: producer outcome **blocked**, caller adapter **blocked**,
typed result **degraded**, probe exit 1. Одинаковый WAV/hash не скрыл различие
в выполнении запросов. Full reports/typed reasons — workflow artifact.

Закрыт execution-scope transport разрыв; всё ещё не приняты полный song/content
результат, установленный GUI и реальные CUDA/AMD GPU профили. Счётчик принятого
в повторном проходе остаётся 20, пакет T0021–T0030 активен.

## Первое техническое typed success реального classic instrumental

Source 795c558f09e693ca1f5fde2a00617ec6b4febfd3:
`prepare_traced_mix` фиксирует identity beat до/после actual mixer и hash mix.
`attach_instrumental_evidence` в canonical finalization проверяет live stage
objects, caller scope, actual files/paths/stereo/duration, trace hashes и master
integrity. Только producer-derived `music_present`; не listening/model test.
Технический typed success не является новым singing/quality/license профилем.

Негативные tests (fixtures): изменённый beat/mix/master, malformed/null hash,
missing trace, vocal used, fallback/failed stage, duplicate stage, outside file,
смена входа во время mixer call. Старый manifest удаляется при провале повторной
проверки. Никакого изготовления manifest из одного существующего legacy WAV.

[Windows 45158238672](https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45158238672):
**SUCCESS все пять job**, настоящий classic positive 20.0 s / 22.3108 s wall /
343875584 bytes sampled RSS; outcome/adapter/typed result **success**.
[Сохранённые manifests и job metadata](restart-hardware-content-windows-45158238672.json).
Actual beat/mix/master SHA сохранены в compact summary. Контрольный requested
texture case остаётся blocked/degraded без manifest, хотя WAV тот же.
Workflow отдельно assert-ит instrumental kind, hash binding и quality_accepted=false.

Локальный расширенный набор после сохранения компактного hardware identity:
**318 Python tests passed**. Повторный Windows run 45158731434 (source
22e22480e85d9266ac47bc5a781c7bff939ee5f1): **SUCCESS все пять job**.
[Durable summary](restart-hardware-provenance-windows-45158731434.json):
CPU AMD64 Family 25 Model 1 / 4 threads / 2 cores / RAM 15.99 GiB;
20.0 s / 27.2780 s wall / 350265344 bytes sampled RSS;
outcome/adapter/typed **success**, `quality_accepted=false`.
Контрольный requested-texture case: blocked/degraded, без render_evidence.
Полный report/WAV — artifact windows-classic-pipeline-diagnostic.
Полный runtime profile, singing, установленный GUI, CUDA/AMD GPU всё ещё не
приняты. Новое техническое instrumental content evidence не закрывает весь пакет.

## Настоящий CPU-артефакт в упакованном Electron renderer

Source `870b45a801c0c62d3e90334854ff5208b9673327`:
`desktop/electron/live-result-check.js` + optional live check в
`window-startup-check.js`. Работает только в диагностическом --window-check
при заданном ZSMM_LIVE_PROBE. Не добавляет обходов обычной генерации/IPC.

Native сторона проверяет revision/source текущего checkout, согласованность
producer/adapter/typed success, instrumental requested kind, quality=false,
привязку master hash к provenance, regular WAV/размер и **заново вычисленный
SHA-256 настоящего файла**. Изменённый WAV, другой source, противоречивые
status/succeeded и невалидная привязка не поступают как успешная envelope.

Затем реальный packaged renderer вызывает свой production isCompleteResult
на настоящей envelope. 6 проверок: instrumental request accepted; singing
request rejected; failed task, failed outcome, cancellation, invalid artifact
rejected. Негативные варианты — мутации реально полученного отчёта, не новые
музыкальные inference. Unit VM-тесты отдельно обозначены как fixtures.

[Windows 45160086121](https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45160086121):
**SUCCESS все пять job**. [Durable reports](restart-hardware-packaged-windows-45160086121.json).
Classic actual CPU: 20.0 s / 22.2324 s wall / sampled RSS 350617600 bytes;
4 threads / 2 cores / RAM 15.99 GiB, default backend CPU. Typed instrumental
success. Master 7056056 bytes, SHA
`ef1018be785fee33aadca425ae2adb47908ac643d9a8c55118f2ec3887ed45cf`.
**Packaged liveInstrumental.ok=true, все 6 checks true**, тот же hash/bytes,
quality_accepted=false. Сгенерирован новый unpacked Electron, без публикации.
Полный window report — artifact output/classic-live-window.json.

Дополнительно plan restart regression 45160035885 на source 91f0382:
оба job SUCCESS, включая прежние packaged help/7 typed fixtures. Не выдаём
этот отдельный source за финальную live probe ревизию 870b45a.
Локально: **41 JS passed**, 17 Python budget/product/plan checks passed;
сам Python render/provenance код не менялся относительно 318-test pass.

Границы: это **win-unpacked packaged renderer**, не установка NSIS/ACL, не
нажатие «сгенерировать» от UI до результата и не запуск рендера bundled Python.
Нет singing, human quality acceptance или CUDA/AMD GPU inference. Нет подписи
и сертификации release binary. Полный T0021–T0030 не закрыт; счётчик 20.

## Настоящие DOM-клики: packaged GUI → IPC → worker → WAV

Source `a29fbd960cf559f4736b7e7c3c0fe30311f38559`:
`desktop/electron/gui-beat-check.js` — диагностический opt-in только в
--window-check + ZSMM_GUI_BEAT_CHECK=1. Не подменяет renderBeat, preload,
IPC handler или Worker. Открывает beat section, заполняет phonk/140/seed7,
вокал none и bank off, кликает production «Собрать бит».

Сначала запускает 120 s запрос и кликает «Отменить» после первого настоящего
IPC progress event. Проверяет возврат кнопок, canceled status и неизменность
предыдущего audio state. Затем через ту же кнопку запускает 20 s retry.
Проверяет реальный worker (не fallback main), отчёт/UI controls, blob player,
полный PCM16 stereo WAV, длительность/peak/RMS/размер/SHA и записывает artifact.
Это программные DOM click events, не ручной человеческий аудит.

[Windows 45161164359](https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45161164359):
**SUCCESS все пять job**. [Durable GUI/CPU reports](restart-hardware-gui-windows-45161164359.json).
`guiBeat.ok=true`, cancellation.clicked=true, progress_count=1,
previous_audio_preserved=true; статус «Рендер отменён — бит не сохранён».
Повтор: «Готово: 6 секций, 20 с. Можно слушать.», save/open enabled,
cancel disabled, player visible/blob. Renderer worker, **20.0 s за 5.5834 s**
после click; весь GUI-check с navigation/cancel/transfer — 5.845 s.
WAV 3528044 bytes, stereo 44100 Hz / 16 bit, peak 0.76837, RMS 0.16898,
SHA `fb1df45ac8b19b275c22f789316364cb7b1f2793c130f3f4cfc2db34cfc4632d`.
Hash совпал со standalone Node worker 20 s этого же source; это единичная
байтовая воспроизводимость, не обещание для всех версий/движков.

Локально 43 JS tests passed и 17 Python budget/product/plan checks passed.
JS fixtures отдельно тестируют отказы validator; не выдаются за GUI execution.
Настоящий GUI-WAV и window report — workflow artifacts:
output/gui-click-instrumental.wav, output/classic-live-window.json.

Границы: только существующий раздел «Бит», JS procedural engine без Python,
voice/samples off, win-unpacked. Это не wizard/agent song generation, не
bundled Python, не NSIS/ACL install. Включение Save/Open проверено, но системный
диалог сохранения/плеер не запускались. Звук не прослушан человеком, общий
RSS всех Electron процессов не измерен. quality/profile accepted=false.
CUDA/AMD GPU и full singing/song не приняты; T0021–T0030 остаётся активным.

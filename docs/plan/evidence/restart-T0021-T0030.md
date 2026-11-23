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

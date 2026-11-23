# Матрица аппаратных возможностей

Полные профили Windows CPU, NVIDIA CUDA и AMD **не приняты**. Наличие адаптера,
установленный backend и успешный inference конкретной модели — разные факты.
Исторические расчёты и цены перенесены в
[архив непроверенных оценок](history/hardware-estimates-unverified.md); использовать
их как минимальные требования или обещание скорости нельзя.

## Проверяемый контракт

- Инвентарь: `python tools/measure_hardware_profile.py --help`. RAM, свободный
  диск и CPU — диагностические измерения, не разрешение на любую модель.
- `preflight_resources` требует явных положительных бюджетов RAM/диска.
  Неизвестное значение, NaN, Infinity, строка и bool не означают «хватает».
- Registry проверяет бюджет VRAM, фактически свободную память backend и запас
  1 GiB. Нулевая оценка модели не разрешает запуск при нулевой свободной VRAM.
- CPU ASR/LLM проверяют свободную RAM перед загрузкой. Оценки модели должны быть
  конечными неотрицательными числами; неизвестная RAM означает отказ.
- ROCm через torch.cuda не доказывает поддержку CUDA-only CTranslate2.
  DirectML/название AMD-адаптера не означают работоспособность модели.

## Воспроизводимый узкий benchmark

`python tools/windows_neural_smoke.py` запускает настоящую Silero CPU сначала
с разрешённым скачиванием, затем из локального пакета. Отчёт содержит версию
Torch, ревизию upstream loader, SHA-256 пакета и WAV, длительность аудио,
wall time, real-time factor и RSS процесса с выборкой каждые 20 ms.
Первый запуск включает загрузку/скачивание; это не чистое время inference.
Выборочная RSS не гарантирует обнаружения кратковременных пиков и не включает
дочерние процессы. Offline-часть запрещает Python socket connect/DNS/sendto;
это **не OS firewall** и не доказательство отсутствия native networking.

Результат относится только к русской черновой **речи** Silero на конкретном
runner. Он не подтверждает пение, музыкальное качество, все модели продукта,
GPU-профиль или лицензионную готовность. Для полного профиля нужны отдельные
измерения реальных пользовательских сценариев на заявленном оборудовании.

### Полученный узкий результат — не полный профиль продукта

[Windows 45143489947](https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45143489947),
source `201d933d39a6703fe8932af9a6da6cbf1914c6c7`: оба job SUCCESS;
76 контрактных тестов и настоящий Silero CPU inference.
Runner: RAM 15.99 GiB, 4 потока, 2 ядра, Torch 2.5.1+cpu, без PyTorch GPU.
Offline: 4.6875 s речи за 6.2315 s wall (включая загрузку модели),
RTF 1.3294, sampled RSS 1049825280 bytes; перехваченных Python-сетевых
обращений 0. [Машиночитаемый протокол](plan/evidence/restart-hardware-windows-45143489947.json).
Это единичный замер, не гарантированная скорость и не минимальные требования.

## Воспроизводимый музыкальный DSP benchmark

```
node tools/desktop_render_benchmark.js 20 output/hardware-dsp-20
node tools/desktop_render_benchmark.js 120 output/hardware-dsp-120
```

Это production desktop worker без Electron GUI: phonk, BPM 140, seed 7,
синтезированный инструментал без sample bank и вокала. Проверяются отмена
реального worker по progress и повтор, затем WAV целиком (формат, длительность,
не тишина, запас пика), записываются SHA-256, время и process lifetime maxRSS.
Wall time включает запуск worker и передачу результата. maxRSS включает
отмену, рендер и проверку, но не GPU/другие процессы. Отдельный Node-процесс
для каждой длительности не смешивает 20-секундный и 120-секундный пики.
`report.json` и WAV — выходы; короткая CI summary не заменяет полный engine
report в artifact. Benchmark не сертифицирует музыкальное качество, нейронную
генерацию, приложение с GUI, минимальную память или отсутствие сетевого трафика.

[Windows 45146340788 — все четыре job SUCCESS](https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45146340788),
source `0df0f88f5d5c03a1001c47615ea7c2689567b4b9`:

| Процедурный инструментал | Wall time | Process lifetime maxRSS |
|---|---:|---:|
| 20 s | 5.8763 s | 262434816 bytes |
| 120 s | 17.2189 s | 895328256 bytes |

Runner CPU различаются (EPYC 7763 и EPYC 9V45, по 4 logical CPUs/16 GiB RAM),
поэтому это не тест линейного масштабирования. Реальная Silero CPU-речь также
прошла в отдельном job; AMD **CPU** не является проверкой AMD **GPU**.
[Полный протокол с источником и хешами](plan/evidence/restart-hardware-windows-45146340788.json).

## Локальная проверка конкретного backend без CPU-подмены

```
python tools/local_model_benchmark.py --backend cuda --trusted-model models/silero/v3_1_ru.pt --sha256 <проверенный_SHA256> --out output/hardware-cuda
```

`--backend` принимает только `cpu`, `cuda`, `rocm`. ROCm использует PyTorch
cuda API, но определяется по `torch.version.hip`: AMD ROCm не выдаётся за
NVIDIA CUDA. DirectML этим инструментом не поддерживается и не сертифицируется.
Для CPU/ROCm меняется только значение `--backend`; нельзя подставлять CPU
после отказа GPU и сохранять прежний GPU-статус.

Порядок проверки:

1. Локальный исполняемый пакет должен существовать; SHA-256 сверяется до
   `PackageImporter`. Хеш не устанавливает доверие: источник весов необходимо
   проверить независимо. Загрузка pickle/package может исполнять код.
2. Проверяется доступность **запрошенного** backend; при несовпадении — отказ
   до вызова модели. Нет скачивания или автоматического CPU fallback.
3. Загружается настоящая Silero, задаётся устройство, синтезируется фиксированная
   русская речь. Проверяются устройство выходного tensor (включая GPU index),
   конечное непустое аудио и WAV. Для GPU обязательны положительные PyTorch
   peak allocated bytes; также сохраняются peak reserved bytes и synchronize.
4. В отчёте есть wall time (загрузка/transfer/inference/CPU conversion/запись WAV),
   sampled RSS, RTF, хеш WAV и пакета, версии и инвентарь. Python socket guard
   действует во время загрузки/синтеза, но не является OS firewall. Он не
   запрещает native networking и не изолирует недоверенный исполняемый пакет.

`inference_verified=true` относится только к этому конкретному синтезу речи;
`product_profile_accepted` всегда false. Устройство выхода и GPU allocations
не являются профилированием каждого kernel и не доказывают, что все внутренние
операции модели были выполнены на GPU. Нет проверки singing, MusicGen, RVC,
полной песни, всего установленного приложения или лицензионной готовности.
`report.json` записывается и при отказе; exit code 1 нельзя превращать в PASS.
Ранее созданный WAV не удаляется при отказе, поэтому его наличие без
`report.ok=true` и совпадающего хеша не является результатом текущего запуска.

Проверка новой утилиты: [Windows 45148490225](https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45148490225)
(source `bb528dad5e6f9e08c1993fb3c058a760623df568`), все четыре job SUCCESS.
Strict CPU: 5.775 s речи за 9.2548 s wall, sampled RSS 909131776 bytes,
RTF 1.6026, Python network attempts 0. GPU-ветки этим прогоном **не испытаны**.
[Сохранённая compact summary](plan/evidence/restart-hardware-strict-windows-45148490225.json).

## Диагностика классического Python-пайплайна

```
python tools/pipeline_hardware_probe.py --duration 20 --out output/new-classic-hardware-run
```

Каталог должен быть новым. Это настоящий procedural CPU-прогон всех стадий
без `only`/dry-run; voice off, stems off, один streaming stand, quality fast.
Он не обещает полный neural/song profile. При blocked/failed outcome код
возврата **1**, даже если сформирован master. Файл учитывается только как
`diagnostic_audio`, а не как успешный продукт. Результат лежит в
`probe_report.json`, подробный pipeline report — в подкаталоге `pipeline`.

[Windows 45149932663](https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45149932663):
20.0 s diagnostic master, 36.9244 s wall, sampled RSS 474902528 bytes,
**outcome blocked, probe exit 1, profile not accepted**. Отдельный CI-job
успешно проверил именно этот отрицательный контракт и реальные OK стадии
mix/master/QA/release. Это не успешная полная приёмка classic pipeline.
[Протокол](plan/evidence/restart-hardware-classic-windows-45149932663.json).

### Успешный classic CPU-запрос без необязательной текстуры

```
python tools/pipeline_hardware_probe.py --duration 20 --without-texture --out output/new-requested-instrumental
```

Новый флаг задаёт в caller recipe `use_texture=false` (по умолчанию true).
С voice off / stems off это ограниченный процедурный инструментальный запрос,
а не обещание выполнения neural стадий. Только явно не запрошенные BLOCKED
стадии учитываются как canonical `not_requested`; ошибки исполнения, QA,
обязательные стадии, dry/partial run не исключаются. Raw статусы не меняются
на OK. Generic adapters не доверяют исключениям из producer report: текущая
приёмка относится к direct classic Python API/probe, не ко всему GUI/result API.

[Windows 45151624994](https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45151624994):
20.0 s master / **27.5456 s wall** / sampled RSS **356839424 bytes**,
probe exit **0**, canonical outcome **success**. С запрошенной, но недоступной
texture тот же WAV по-прежнему даёт blocked/exit 1. Это не GPU-профиль,
не пение и не полная сертификация продукта.
[Протокол](plan/evidence/restart-hardware-scope-windows-45151624994.json).

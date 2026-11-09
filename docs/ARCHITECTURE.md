# Архитектура ZS Music Maker

> Версия: 41.0.0-alpha.16. Документ описывает **фактическое** устройство кода.
> Если код и документ расходятся — прав код, документ правится в том же коммите.
>
> Пофайловый состав и статус каждого модуля — `docs/PROJECT_INVENTORY.md`;
> процесс изменений — `docs/WORKFLOW.md`.

## 1. Слои

```
main.py                     точка входа: маршрутизация флагов + запуск GUI (138 строк)
app/cli/                    CLI-слой: env (версия/кодировка), parser, commands, gui, backup, probes
config/settings.py          конфиг: env > .env > дефолты (ZSMM_*)
app/core/                   инфраструктура: логи, контракты, безопасность, бэкапы
app/ai/                     AI-слой: реестр моделей, sequential runner, quality gates, prompts
app/pipeline/               контракт стадии: StageStatus, StageResult, classify(), summarize()
app/core/recipe.py          состояние визарда → нормализованный рецепт трека
app/core/stages/            стадии классического пайплайна (prep/beat/texture/lyrics/vocal/mix/master/release)
app/core/ai/                стадии AI-пайплайна (meta/music/vocal/final) + render-хелперы
app/core/orchestrator.py    склейка классического DSP-пайплайна (15 стадий, 350 строк)
app/core/pipeline_blocks.py  блоки пайплайна: вход, бит, текст, вокал, микс, пост, релиз
app/core/pipeline_runtime.py тайминг/статусы стадий, seed, --only/--resume
app/core/stages/vocal_chain.py вокальная ветка: своя запись → TTS → RVC → FX
app/core/orchestrator_god.py  God Mode (5 стадий, чекпоинты)
app/core/orchestrator_ai.py   AI-пайплайн: только проводка стадий через SequentialAIRunner
modules/                    аудио/текст/релиз/диагностика — прикладные модули
  beat/ llm/ lyrics/ hit_scorer/ release/ artist_dossier/  — пакеты по ответственности
agents/                     источники: сэмплы, тренды, сленг
app/gui/                    PySide6: wizard (5 шагов), тема, онбординг
tools/                      обслуживание: readiness, аудиты, smoke, e2e
tests/                      pytest: unit / audio / e2e
```

Правило: **`main.py` не содержит тяжёлой логики**, `modules/` не знает про GUI,
`app/gui/` не знает про конкретные DSP-модули напрямую (только через оркестратор).

## 2. Классический пайплайн (`app/core/orchestrator.run_full_pipeline`)

| # | Стадия | Артефакт |
|---|---|---|
| 1 | `_stage_analyze` | BPM/ключ/агрессия из референсов (librosa) или жанровый дефолт |
| 2 | `_stage_groove` | groove-шаблон (ударные паттерны + swing) |
| 3 | `_stage_arrangement` | план аранжировки (секции, длина) |
| 4 | `_stage_beat` | `beat.wav` (beat_constructor / synth fallback) |
| 5 | `_stage_texture` | атмосферная текстура (MusicGen → BLOCKED → scaffold) |
| 6 | `_stage_lyrics` | текст (+ структура), LLM → шаблон → user_lyrics |
| 7 | `_stage_voice_synth` | вокал (Silero → XTTS → bark → pyttsx3) или BLOCKED |
| 8 | `_stage_rvc` | конверсия голоса (только при наличии `.pth`) |
| 9 | `_stage_vocal_fx` | дабл, delay-throw, чистка |
| 10 | `_stage_mix_and_sidechain` | `mix.wav` (bus = beat + vocal, ducking по кику) |
| 11 | `_stage_mastering` | 8 стендов (`mastering.master_all_stands`) |
| 12 | `_stage_polish` | anti-neuro (`anti_neuro` → `anti_ai_polish` → копия) |
| 13 | `_stage_stems` | стемы (Demucs → BLOCKED) |
| 14 | `_stage_hit_score` | hit-score + рекомендации |
| 15 | `_stage_release_pack` | релиз-пакет (~38 файлов) |

Каждая стадия возвращает `app.pipeline.StageResult` со статусом
`OK | FALLBACK | BLOCKED | FAILED` (плюс `reason`, `attempts`, `duration_sec`).
`OK` и `FALLBACK` — полноценный результат, `BLOCKED` — честный пропуск из-за
отсутствующей тяжёлой зависимости (половинный зачёт в `percent`),
`FAILED` — поломка (ноль). Итог считает только `app.pipeline.summarize()`:
Verdict `PASS | PASS_WITH_FALLBACK | PASS_BLOCKED | BLOCKED_SIMULATION | PARTIAL`.
Симуляция (синтетическая заглушка вне BLOCKED) ограничивает `percent` 60.

Прогресс наружу отдаётся колбэком `on_stage(name, status, index, total)`:
`app/runtime_orchestrator.py` переводит его в `job.progress`, поэтому полоска
в визарде движется по факту выполнения стадий, а не по «0.1 → 0.92».
`total` — длина `STAGE_RECORDS`: пропущенная стадия тоже добавляется в список
(со статусом `BLOCKED`), поэтому счётчик всегда совпадает с фактическим отчётом.
Частичный прогон задаётся списком `only` в рецепте (`null` — полный прогон):
именно так работает «пересобрать только вокал/мастер».

Рецепт трека собирается один раз (`app/core/recipe.py`) из состояния визарда:
пресет, BPM, жанр, агрессия, число куплетов, стенды, вокальный режим, свои
строки и своя запись с микрофона (`own_vocal_wav` — основной вокальный путь,
TTS/RVC только fallback).

### Входы, а не копии

`--god` (`app/core/orchestrator_god.py`) и `--async`
(`app/core/orchestrator_async.py`) — **адаптеры** над тем же
`run_full_pipeline`, а не отдельные конвейеры. God задаёт длину 120 с и
переводит отчёт в прежнюю форму (`status/stages/master_path/vocal_status`);
async исполняет тот же прогон в рабочем потоке, чтобы не блокировать event
loop, и отдаёт стадии списком `AsyncStage`. Раньше у каждого входа был свой
порядок стадий и своя цель громкости (−12 LUFS у god), из-за чего правки
качества до них не доезжали; теперь новая стадия добавляется в одном месте.

### Барабаны: банк + синтез

`modules/beat/voices.py` берёт кик/снейр/клэп/хэты из `data/samples`
(CC0 one-shot'ы, см. `data/samples/README.md`), а саб-хвост кика в дропе и
ноты баса строит синтез: затухающий one-shot не держит ноту на такт.
Калиброванные тримы `drums.BANK_GAIN` компенсируют разницу «пик против
громкости» между записями и синтезом; баланс и crest нового бита отличаются
от синтезированного и требуют прослушивания. Отчёт движка честно называет источник:
`sample_bank+procedural` / `REAL_PASS`, а если банка нет — `FALLBACK`.

### Мастеринг: один пакет, пять файлов

`modules/mastering/` — `targets.py` (цели LUFS/crest/корреляции и EQ по
стендам), `loudness.py` (бисекция по усилению + доводки), `chain.py`
(`master_one`: тон → компрессия → лимитер → crest → гейты), `normalize.py`
(догнать громкость уже готового мастера) и `stands.py` (все стенды + отчёт).
Публичный вход — `from modules import mastering` (реэкспорт без изменений).

### Мастеринг стендов считается параллельно

Восемь стендов независимы, поэтому `master_all_stands` раскладывает их по
процессам (`ProcessPoolExecutor`, до `min(cpu_count, 4)` воркеров;
`ZSMM_MASTER_WORKERS=1` — принудительно последовательно, при недоступности
пула — честный фолбэк на последовательный счёт). Результат побитово совпадает
с последовательным (`tests/test_mastering_parallel.py`): измерено на 120-секундном
треке — 349.5 с → 180.9 с на двух ядрах, на 8-ядерной машине ускорение
ближе к линейному. `main.py` вызывает `multiprocessing.freeze_support()`,
иначе собранный exe при порождении процессов перезапускал бы сам себя.

### Переключатели, влияющие на звук

| Переменная | По умолчанию | Что меняет |
|---|---|---|
| `ZSMM_ARRANGEMENT_DRIVES_BEAT` | `1` | структура трека решается в аранжировке и передаётся биту; `0` — прежнее независимое планирование бита, бит-в-бит |
| `ZSMM_MASTER_WORKERS` | `0` (авто) | число процессов мастеринга; `1` — последовательно, результат побитово тот же |
| `quality_mode` (визард) | `quality` | `fast`/`quality`/`max`: размер MusicGen и число итераций доводки громкости (`1`/`3`/`5`) |

## 3. AI-слой

- `app/ai/registry.py` — 13 ролей: engine, hf_repo, файл, SHA-256, VRAM/RAM.
  Одна тяжёлая модель в памяти; `registry.use(key)` — контекст-менеджер.
- `app/ai/sequential_runner.py` — последовательный запуск стадий, watchdog
  по таймауту (SIGALRM на POSIX), VRAM-ceiling (OOM), телеметрия.
- `app/ai/quality/` — валидаторы артефактов. Стадия не отдаёт `ok=True`,
  пока файл не прошёл гейт (мастер: true-peak ≤ −1 dBTP; обложка ≥ 512 px RGB;
  текст: длина/уникальность/структура; аудио: длительность/каналы/пик/RMS).
- `app/ai/prompts.py` + `data/prompts/*.txt` — каталог промптов по ролям.

## 4. Данные

| Путь | Что | Версионируется |
|---|---|---|
| `data/genre_presets/`, `config/genres_100.json` | пресеты жанров (50 JSON) и каталог 100 жанров | да |
| `data/prompts/` | промпт-ассеты ролей | да |
| `data/artist_dossier/` | схема досье артиста (`schema.json`) | да |
| `data/samples/` | 32 CC0 one-shot'а TR-808 и трёх наборов BOOCHI44 + `manifest.json` (лицензия, источник, SHA-256, tuning_hz) и `ATTRIBUTION.md`; собирается `tools/import_samples.py`, проверяется `tools/samples_audit.py` | да (только CC0/лицензионно чистое) |
| `data/ai_models/` | веса моделей | **нет** (тянутся локально) |
| `output/`, `logs/` | результаты рендера и логи | нет |
| `voice_vault/`, `lyric_vault/`, `references/` | пользовательские данные | нет |

## 5. Контракты

- Результат прогона: `{project_id, verdict, percent, stages[], warnings[], master_path}`.
- AI-прогон дополнительно пишет `manifest.json` schema v1 (seed, роли, хеши).
- Любой отказ — словарь с `ok: False` и человекочитаемым `reason`.
- Детерминизм: `seed` → идентичный артефакт (кроме стадий с явным `ai=True`).

## 6. Журнал и крэш-репорты

Единственная реализация — `app/core/logger.py` (прежний `app/logger.py` удалён:
он писал в `logs/` относительно текущего каталога, из-за чего при запуске с
ярлыка журналы терялись).

- каталог: `ZSMM_LOG_DIR` → `%LOCALAPPDATA%\ZS Music Maker\logs` (Windows) →
  `~/.local/share/zs-music-maker/logs` → `<проект>/output/logs` → temp;
- `app.log`, ротация 10 МБ × 5; `setup_logger()` идемпотентен (нет дублей хендлеров);
- фильтр `redact_secrets` вычищает токены/ключи до записи;
- `SafeStream` не падает на cp866-консоли; `ZSMM_SILENT_CONSOLE=1` гасит консоль;
- `install_excepthook()` пишет `crash_YYYYmmdd_HHMMSS.txt` с трейсбеком и
  окружением и вызывает прежний обработчик; визард ставит его с контекстом
  `desktop-wizard`.

## 7. Упаковка и запуск

- `packaging/zsmm.spec` — PyInstaller onedir (onefile только при `ZSMM_ONEFILE=1`:
  onefile распаковывается при каждом старте и не даёт обещанного «старт < 5 с»),
  `console=False`, в бандл попадают `data/`, `docs/`, `scripts/`, `version.json`,
  `VERSION`, `INSTALL.md`, `LICENSE`; тяжёлые пакеты (torch, audiocraft, demucs,
  TTS, bark, gradio) исключены.
- `scripts\build_exe.cmd` собирает и сразу прогоняет `--version` у собранного exe.
- `scripts\setup.cmd` (проверка Python ≥ 3.11, venv, зависимости, `--health`),
  `scripts\run_silent.cmd` (pythonw, без окна консоли), `scripts\run.cmd`
  (с консолью), `scripts\verify.cmd` (compileall → pytest → смоуки → аудиты →
  `--version`/`--readiness`), `scripts\make_shortcut.ps1` (ярлык на exe или
  на `run_silent.cmd`).
- `desktop/` — окно на Electron: `electron/main.js` (окно, IPC, безопасность),
  `electron/preload.js` (единственный мост, `contextIsolation: true`),
  `electron/tasks.js` (белый список задач: окно не может запустить произвольный
  процесс), `src/core/*` (жанры, пресеты, inventory, расчёт готовности),
  `src/app.js` (разделы «Обзор», «Модули», «Жанры», «Бит», «Досье»,
  «Запуск», «Диагностика»). Данные читаются из файлов проекта; числа
  готовности готовит `npm run snapshot` вызовом штатного
  `python -m tools.readiness`, и окно **сверяет** их с собственным расчётом.
  Звук считает тоже окно: `src/core/audio/*` — порт `modules/beat/` на
  JavaScript (синтез ударных, сэмпловый банк `data/samples/` с декодером WAV,
  фильтры Баттерворта, ритм и акценты, гармония, драматургия, сборка и запись
  WAV). Python остаётся эталоном и
  источником тяжёлых моделей: свои задачи окно запускает той же командой,
  что и терминал, и показывает вывод построчно. Упаковка описана в
  `package.json` (`electron-builder`), но инсталлятор не собирался: в
  окружении сборки нет Electron и целевых платформ.

## 8. Проверки

| Команда | Что ловит |
|---|---|
| `python -m pytest tests/` | 2032 теста: unit, аудио, e2e, property, контракты GUI/CLI, порт движка в окно |
| `python tools/smoke_audio.py` | стерео, громкость, drop (6 проверок) |
| `python tools/smoke_god.py` | God Mode E2E, master 120 с, true-peak (8 проверок) |
| `python tools/fallback_audit.py` | fallback-пути и маркеры заглушек |
| `python -m tools.audit_honesty` | фейковые успехи и немые `except` |
| `python tools/gitignore_guard.py` | код, случайно попавший под `.gitignore` |
| `python tools/ast_dead_imports.py` | мёртвые импорты |
| `python tools/ast_undefined_names.py` | имена, использующиеся без определения (`NameError`) |
| `python -m tools.readiness` | честный процент готовности + матрица модулей |
| `cd desktop && npm test` | 416 тестов оболочки на Electron: каталог, готовность, задачи, рендер окна в DOM-двойнике, аудио-движок (фильтры против чисел scipy, детерминизм seed, WAV, сэмпловый банк, замеры «формульности», пошаговый рендер), пути установленного приложения, рендер в worker, настройки, описание сборки Windows, политика окна (AppUserModelId, единственный экземпляр, меню), вокал (формантный синтез с измерением формант и попадания в ноту, мелодия по тональности, тестовые дубли и проверка честности источника), запись с симулированного входа (сигнал → PCM → WAV → чтение обратно), подпись кода (конфигурация из секретов и проверка Authenticode), правка досье без Python, общая область видимости скриптов окна (как в браузере) — пакет `electron` не нужен |
| `python -m pytest tests/test_desktop_audio_port.py` | сверка JS-таблиц ритма и акцентов с `modules/beat/patterns.py`, проекция 120 жанров, чтение готового WAV через `soundfile` |
| `cd desktop && npm run snapshot` | снимок чисел через штатный Python-инструмент → `data/desktop/` |
| `python -m pytest tests/test_desktop_shell.py` | сверка расчёта готовности в JS с эталоном Python |

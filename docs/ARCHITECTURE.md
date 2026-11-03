# Архитектура ZS Music Maker

> Версия: 41.0.0-alpha.15. Документ описывает **фактическое** устройство кода.
> Если код и документ расходятся — прав код, документ правится в том же коммите.

## 1. Слои

```
main.py                     точка входа: маршрутизация флагов + запуск GUI (111 строк)
app/cli/                    CLI-слой: env (версия/кодировка), parser, commands, gui, backup, probes
config/settings.py          конфиг: env > .env > дефолты (ZSMM_*)
app/core/                   инфраструктура: логи, контракты, безопасность, бэкапы
app/ai/                     AI-слой: реестр моделей, sequential runner, quality gates, prompts
app/pipeline/               контракт стадии: StageStatus, StageResult, classify(), summarize()
app/core/recipe.py          состояние визарда → нормализованный рецепт трека
app/core/stages/            стадии классического пайплайна (prep/beat/texture/lyrics/vocal/mix/master/release)
app/core/ai/                стадии AI-пайплайна (meta/music/vocal/final) + render-хелперы
app/core/orchestrator.py    склейка классического DSP-пайплайна (15 стадий, 339 строк)
app/core/pipeline_runtime.py тайминг/статусы стадий, seed, --only/--resume
app/core/stages/vocal_chain.py вокальная ветка: своя запись → TTS → RVC → FX
app/core/orchestrator_god.py  God Mode (5 стадий, чекпоинты)
app/core/orchestrator_ai.py   AI-пайплайн: только проводка стадий через SequentialAIRunner
modules/                    аудио/текст/релиз/диагностика — прикладные модули
  beat/ llm/ lyrics/ hit_scorer/ release/ artist_dossier/  — пакеты по ответственности
agents/                     источники: сэмплы, тренды, сленг
app/gui/                    PySide6: wizard (9 шагов), тема, онбординг
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

## 3. AI-слой

- `app/ai/registry.py` — 13 ролей: engine, hf_repo, файл, SHA-256, VRAM/RAM.
  Одна тяжёлая модель в памяти; `registry.use(key)` — контекст-менеджер.
- `app/ai/sequential_runner.py` — последовательный запуск стадий, watchdog
  по таймауту (SIGALRM на POSIX), VRAM-ceiling (OOM), телеметрия.
- `app/ai/quality.py` — валидаторы артефактов. Стадия не отдаёт `ok=True`,
  пока файл не прошёл гейт (мастер: true-peak ≤ −1 dBTP; обложка ≥ 512 px RGB;
  текст: длина/уникальность/структура; аудио: длительность/каналы/пик/RMS).
- `app/ai/prompts.py` + `data/prompts/*.txt` — каталог промптов по ролям.

## 4. Данные

| Путь | Что | Версионируется |
|---|---|---|
| `data/genres/`, `data/genre_presets/` | жанры и пресеты (JSON) | да |
| `data/prompts/` | промпт-ассеты ролей | да |
| `data/schema/` | схемы (досье артиста и т.п.) | да |
| `data/samples/` | сэмпловая база + manifest с лицензиями | да (только CC0/лицензионно чистое) |
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

## 8. Проверки

| Команда | Что ловит |
|---|---|
| `python -m pytest tests/` | 512 тестов: unit, аудио, e2e, property, контракты GUI/CLI |
| `python tools/smoke_audio.py` | стерео, громкость, drop (6 проверок) |
| `python tools/smoke_god.py` | God Mode E2E, master 120 с, true-peak (8 проверок) |
| `python tools/fallback_audit.py` | fallback-пути и маркеры заглушек |
| `python -m tools.audit_honesty` | фейковые успехи и немые `except` |
| `python tools/gitignore_guard.py` | код, случайно попавший под `.gitignore` |
| `python tools/ast_dead_imports.py` | мёртвые импорты |
| `python -m tools.readiness` | честный процент готовности + матрица модулей |

# PLAN v41 — MASTER PLAN: «Из прототипа в инструмент»

> Статус: **draft / на утверждение**
> Область: весь репозиторий `ttklon/ZS-MUSIC-MAKER`
> Платформа-цель: **Windows 11, один ПК, полностью локально**
> Источник фактов: аудит ветки `main` @ `59c322f` (2026-08-22), см. §2.

---

## 1. Паспорт

### 1.1 Что программа делает сейчас (as-is)

Локальная «хит-фабрика»: из темы + жанра + референсов собирает трек — процедурный бит,
TTS-вокал, микс с сайдчейном, мастеринг под 8 стендов, обложку, тексты, метаданные и
релиз-пакет ~38 файлов. CLI (`main.py`) + PySide6-визард (9 шагов) + Gradio + консоль.
Три параллельных пайплайна (classic / God Mode / AI), 13 зарегистрированных AI-ролей,
честные `BLOCKED` вместо фейкового успеха.

### 1.2 Что должно быть после v41 (to-be)

- **Один** пайплайн, **одна** ответственность на модуль, **один** формат результата стадии.
- Трек, который на слух не отличается от «живого»: реальная сэмпловая база, грув с
  humanize, аранжировка с энергетической драматургией, вокал (свой или TTS/RVC),
  микс и мастеринг по стемам — а не «синтез с нуля из синусов».
- Запуск на Windows 11 в один клик, понятный прогресс, воспроизводимость по seed.
- Репозиторий без мусора: исходники + данные + тесты + 4 документа. Никаких
  сгенерированных дампов и пользовательского состояния в git.

### 1.3 Главный критерий приёмки всей программы

> 5 треков в 5 разных жанрах, собранных одной командой на Windows 11,
> проходят объективные гейты (§7.2) и **слепое прослушивание**: слушатель не может
> определить, что трек собран программой.

---

## 2. Факты аудита (на чём основан план)

| Метрика | Сейчас | Цель v41 |
|---|---:|---:|
| Файлов в git | 1 657 | ~320 |
| `docs/` | **1 168 файлов / 52 МБ** (из них 1 017 файлов, 37 МБ — сгенерированные дампы `docs/PLAN_v39/APP_L_*`: AST-дампы, grep-трафики, история коммитов) | 4 файла + `docs/archive/` |
| `PLAN_v38_AI_MEGA.txt` | 11 МБ | удалить/архив |
| `SESSION_LOG.md` | 115 КБ | `CHANGELOG` + `docs/history/` |
| `docs/STEP_STATUS/` | 144 файла | 0 (свернуть в историю) |
| Production `.py` | 158 | ~60 |
| Тест-функций | 312 в 98 файлах | ~120 в ~40 файлах, по пирамиде |
| Модулей без статических ссылок | **26** | 0 |
| Модулей только с тестовыми ссылками | 16 | 0 (либо в продукт, либо вон) |
| Реализаций мастеринга | 6 | 1 + адаптер matchering |
| Оркестраторов/пайплайнов | 6 + 5 legacy-патчей | 1 + 1 legacy-адаптер (опц.) |
| Реализаций «вокала» | 13 | 6 (engine chain, vault, rvc, fx, cleaner, recorder) |
| Логгеров | 2 | 1 |
| Жанровых паттернов бита в коде | **3** (phonk/trap/house) | 120 (JSON) |
| Жанровых пресетов в данных | 50 | 120 |
| Захардкоженных RU-строк | 1 518 | 100 % через i18n |
| i18n охват | 3 файла | весь UI/CLI |
| Трекаемое runtime-состояние | `lyric_vault/*`, `voice_vault/*`, `data/hw_profile.json`, `data/tutorial_settings.json`, `training_texts/progress.json` | 0 |
| Тесты, реально запускаемые | не запускаются (нет env; CI красный) | `pytest -q` зелёный на Win+Linux |
| `python -m compileall` | **1 SyntaxError** (`tools/readiness.py:528`) | 0 |

**P0-дефекты, найденные аудитом (чинятся в Этапе 0):**

1. `tools/readiness.py:528` — f-string с `\\|` → `SyntaxError` на Python ≤ 3.11. Ломает
   `--readiness`, шаг `compileall` в CI и три тест-модуля (collection error).
2. CI на `main` красный с v40: задания падают за 2–4 с с пустым списком шагов и пустым
   `runner_name` — инфраструктура/квота Actions, а не код. Зелёных прогонов нет вообще.
3. Рассинхрон: `version.json`/`VERSION` = 39.9.0, коммит и CHANGELOG — «v40»,
   `PROJECT_STATE.md` декларирует 147 модулей / 141 тест / 26 тест-файлов (факт: 158 / 312 / 98).
4. `.gitignore` игнорирует `*.json` целиком с ручными исключениями → новые data-JSON
   молча не попадают в репозиторий; `data/hw_profile.json` и `data/tutorial_settings.json`
   одновременно отслеживаются и находятся в игноре.

---

## 3. Принципы (правила, чтобы не повторить «плохого ИИ»)

1. **Одна ответственность — один модуль.** Никаких `*_v2.py`, `*_v9.py`, `*_final.py`.
   Изменение = правка существующего файла, а не новый слой.
2. **Никакого «третьего» пайплайна.** Новая возможность = новая стадия в общем реестре,
   а не новый оркестратор.
3. **Один контракт результата**: `StageResult(status, artifacts, metrics, reason, duration)`.
   Статусы: `OK | FALLBACK | BLOCKED | FAILED`. Нет исключений.
4. **Гейт на выходе обязателен.** Артефакт без валидатора не передаётся дальше.
5. **Детерминизм**: любой рендер воспроизводим по `seed`; тест сравнивает хеш WAV.
6. **Никакого фейкового успеха.** Отсутствующие веса/пакеты → `BLOCKED` с причиной.
7. **Размер файла ≤ 400 строк**, функция ≤ 60 строк. Иначе — декомпозиция.
8. **Windows-first.** Каждый этап заканчивается прогоном на Windows 11.
9. **Удаляем только после зелёных тестов.** Каждое удаление — отдельный коммит с причиной.
10. **Документация — часть кода**: изменил поведение → изменил `CHANGELOG` в том же коммите.

---

## 4. Целевая структура репозитория

```
main.py                     # тонкий CLI-фасад (~150 строк): парсинг → вызов app.cli
app/
  cli/            commands.py, render.py, tools.py
  core/           config, logger, errors, contracts (StageResult), security
  pipeline/       runner.py, registry.py, stages/*.py, cache.py
  audio/          beat/, vocal/, mix/, master/, dsp/, samples/
  text/           lyrics.py, memory.py, author_style.py, llm.py
  ai/             registry.py, runner.py, quality.py, prompts.py
  sources/        samples.py, trends.py, freesound.py
  release/        pack.py, export.py, isrc.py, licenses.py
  hw/             detect.py, budget.py
  ui/             wizard/, theme.py, i18n.py, onboarding.py
  diagnostics/    health.py, kpi.py, self_diag.py
data/               genres/*.json (120), presets/*.json, samples/manifest.json,
                    prompts/*.txt, schema/*.json
models/             .gitkeep + README (веса не в git)
tests/              unit/, audio/, e2e/, fixtures/
tools/              3–5 скриптов обслуживания (не 25)
docs/               README → ARCHITECTURE.md, WORKFLOW.md, CHANGELOG.md, PLAN_v41_MASTER.md
.github/workflows/  ci.yml (linux fast + windows smoke), build.yml (EXE + release)
scripts/            run.cmd, install.cmd, verify.cmd (Windows),Makefile-аналог для Linux
```

---

## 5. Этапы работ

Порядок жёсткий: **0 → 1 → 2 → 3 → 4 → 5 → (6 ‖ 7) → 8**.
Этап 4 — самый большой и главный; всё остальное существует, чтобы он был возможен.

---

### Этап 0. Инженерная база и «зелёный ноль» (1 день)

| ID | Задача | Приёмка |
|---|---|---|
| 0.1 | Починить `tools/readiness.py:528` (вынести escape из f-string) | `compileall` = 0 ошибок на Python 3.11 |
| 0.2 | Рабочее окружение: `requirements` → lock (`pip-tools`/`uv`), Python 3.11, venv-скрипт для Windows | `scripts/setup.cmd` ставит за < 10 мин |
| 0.3 | Починить CI: разобраться с отказом раннеров; разнести `ci.yml` (linux: unit ≤ 3 мин) и `ci-windows.yml` (GUI/EXE smoke) | зелёный прогон на `main` |
| 0.4 | `pytest.ini`: маркеры `unit/audio/e2e/slow/gui`, `--strict-markers`, `-p no:cacheprovider` | `pytest -q -m unit` < 60 с |
| 0.5 | Синхронизировать версию (39.9.0 → 41.0.0-dev), `PROJECT_STATE.md` — генерируемый скриптом | тест консистентности версии проходит |
| 0.6 | Зафиксировать базовые метрики: `tools/metrics.py` (LOC, модули, тесты, время пайплайна) | отчёт в `docs/metrics.md` |

**Выход:** репозиторий собирается, тесты запускаются, CI зелёный, версия честная.

---

### Этап 1. Расчистка мусора (2 дня)

| ID | Что | Куда |
|---|---|---|
| 1.1 | `docs/PLAN_v38_AI_MEGA.txt` (11 МБ), `docs/PLAN_v39/**` (1 017 файлов, 37 МБ), `docs/PLAN_v39_AI_MEGA.txt` (3.5 МБ) | удалить; в `docs/archive/README.md` — одна страница «что было и почему удалено» |
| 1.2 | `docs/STEP_STATUS/*` (144 файла) | свернуть в `docs/history/v39_steps.md` (оглавление + ссылки на коммиты) |
| 1.3 | `docs/LICENSES.md` (116 КБ, генерируется) | генерировать по требованию, из git убрать |
| 1.4 | `SESSION_LOG.md` (115 КБ) | `docs/history/SESSION_LOG_v39.md`; новый журнал — только `CHANGELOG.md` |
| 1.5 | Трекаемое пользовательское состояние: `lyric_vault/*` (кроме `.gitkeep`), `voice_vault/*`, `training_texts/progress.json`, `data/hw_profile.json`, `data/tutorial_settings.json` | удалить из git, добавить в `.gitignore` |
| 1.6 | `.gitignore`: убрать глоб `*.json`, перейти на allowlist `data/**` | `git status` чист после запуска программы |
| 1.7 | 26 модулей без ссылок + 16 test-only (см. §6) | по одному: удалить / назначить канон |
| 1.8 | Корневые скрипты: `run.bat`, `run_all_smoke.bat`, `run_all_smoke.sh`, `verify.bat`, `autodetect_python.bat`, `create_desktop_shortcut.ps1` | свести в `scripts/` (3 файла) |
| 1.9 | Дубли данных: `config/genres_100.json` + `data/genre_presets/*.json` + внутренние пресеты `genre_engine` | один формат `data/genres/<slug>.json` |

**Приёмка:** `git ls-files | wc -l` ≤ 400, размер рабочего дерева ≤ 20 МБ без `.git`,
`pytest` зелёный, ни один запуск программы не создаёт изменений в git.

---

### Этап 2. Дедупликация архитектуры (5 дней)

Матрица «семейство → канон → что удаляется». Точные списки уточняются на старте этапа
автоматическим отчётом `tools/dup_report.py` (построить в 2.1).

| Семейство | Сейчас | Канон v41 | Удаляется |
|---|---|---|---|
| Оркестрация | `orchestrator.py`, `_god`, `_ai`, `_async`, `pipeline_core.py`, `master_pipeline_v12.py`, `runtime_orchestrator.py`, `orchestrator_v8..v12_patch.py` | `app/pipeline/runner.py` + `registry.py` + `stages/*` | 11 файлов, legacy — в опциональный адаптер |
| Мастеринг | `mastering.py`, `mastering_v9.py`, `mastering_pro.py`, `mastering_ai.py`, `matchering_master.py` | `app/audio/master/mastering.py` + `matchering_adapter.py` | 4 |
| Бит | `beat_constructor.py`, `beat_gen.py`, `beat_gen_ai.py`, `cyber_synth.py`, `phonk_engine.py`, `phonk_engine_v2.py`, `midi_generator.py`, `chanson_engine.py`, `arrangement_engine.py`, `groove_extractor.py` | `app/audio/beat/{patterns,synth,samples,arrangement,groove}.py` | 5–6 |
| Вокал | `voice_synth.py`, `voice_synth_ai.py`, `voice_convert.py`, `voice_cleaner.py`, `voice_recording.py`, `voice_vault.py`, `voice_onboarding.py`, `rvc_manager.py`, `rvc_trainer.py`, `anti_neuro.py`, `anti_ai_polish.py`, `vocal_fx.py`, `female_backing.py`, `phoneme_coverage.py` | `app/audio/vocal/{engines,vault,rvc,fx,cleaner,recorder}.py` | 8 |
| Текст | `lyrics_gen.py`, `lyrics_gen_v8.py`, `lyrics_gen_ai.py`, `author_ref_lyrics.py`, `llm.py`, `lyric_vault.py` | `app/text/{lyrics,memory,author_style,llm}.py` | 3 |
| Источники | `sample_hunter.py`, `sample_hunter_v9.py`, `trend_scout.py`, `trend_scout_v3.py`, `freesound_client.py` | `app/sources/{samples,trends}.py` | 3 |
| Железо | `app/core/hw_autodetect.py`, `modules/hw_directml.py`, `app/hw_probe.py` | `app/hw/detect.py`, `budget.py` | 2 |
| Логирование | `app/logger.py` + `app/core/logger.py` | `app/core/logger.py` | 1 |
| UI | `wizard.py`, `wizard_v8_extensions.py`, `theme.py`, `theme.py`, `onboarding.py`, `modules/onboarding.py`, `ui/tutorial.py`, `ui/karaoke_recorder.py`, `expert_mode.py`, `wizard_v12_integration.py` | `app/ui/` (5 модулей) | 4 |
| Релиз | `release_export.py`, `release_pack_v9.py`, `release_pack_full.py`, `distribution.py`, `provenance.py`, `license_manager.py`, `isrc.py` | `app/release/` | 3 |
| Жанры | `genre_engine.py`, `genre_expansion_100.py`, `config/genres_100.json` | `app/genres.py` + `data/genres/*.json` | 1 |
| Диагностика | `health.py`, `self_diag.py`, `kpi_dashboard.py`, `kpi_monitor.py`, `auto_qa.py`, `global_audit_fixer.py` | `app/diagnostics/` | 3 |
| Утилиты разработчика | 25 файлов в `tools/` | 4: `readiness.py`, `audit.py`, `smoke.py`, `genres.py` | 21 |

| ID | Задача | Приёмка |
|---|---|---|
| 2.1 | `tools/dup_report.py`: карта импортов, дубли ответственности, мёртвые модули | отчёт воспроизводим, входит в CI |
| 2.2 | Ввести `StageResult` + `app/core/contracts.py`, перевести на него все стадии | mypy-clean (или `pyright basic`) |
| 2.3 | Переписать пайплайн как DAG с явными входами/выходами стадий | старый и новый результат совместимы по артефактам |
| 2.4 | Слить семейства по матрице (по одному коммиту на семейство) | после каждого — `pytest -m unit` |
| 2.5 | Удалить legacy-патчи v8–v12; при необходимости — один `legacy_adapter.py` с явным флагом | `--legacy-off` больше не нужен |
| 2.6 | Единый `handle`-протокол моделей (load/generate/unload) | одна точка загрузки в `app/ai/registry.py` |

**Приёмка:** production-модулей ≈ 60, ни одного модуля без статической ссылки,
`tools/dup_report.py` = 0 «дублей ответственности», e2e даёт тот же набор артефактов.

---

### Этап 3. Пайплайн, кэш, воспроизводимость (4 дня)

| ID | Задача | Приёмка |
|---|---|---|
| 3.1 | Кэш стадий по хешу (вход + seed + версия) в `output/.cache` | повторный рендер того же рецепта < 5 с |
| 3.2 | `--seed`, `--resume`, `--only <stage>`, `--from <stage>`, `--jobs N` | документировано и покрыто тестами |
| 3.3 | Прогресс-модель: стадия, %, ETA, VRAM, лог в файл | GUI и CLI показывают одно и то же |
| 3.4 | Единая отчётность прогона: `run.json` (manifest v2: версии, seed, хеши артефактов) | воспроизведение по `run.json` на другой машине |
| 3.5 | Ошибки: типизированные исключения + код выхода (0/2/3/4) | CI различает «нет данных» и «сломалось» |

---

### Этап 4. Качество звука — «как настоящий трек» (10–12 дней, ядро проекта)

Цель этапа: убрать «синтетический» окрас и выйти на уровень «человеческий трек из
референс-плейлиста». Работа идёт слоями снизу вверх, каждый слой — со своим гейтом.

#### 4.1 Сэмпловая база (фундамент)
| ID | Задача |
|---|---|
| 4.1.1 | `data/samples/` + `manifest.json`: kick, snare, clap, hat, 808, one-shots, foley, fx — только CC0/лицензионно чистые (поле license, source, sha256) |
| 4.1.2 | `app/audio/samples.py`: загрузка, pitch/время-стретч, velocity-слои, round-robin (анти-«машинное» повторение) |
| 4.1.3 | `fallback`: если сэмплов нет — синтез (текущий `cyber_synth`), но **помеченный** `FALLBACK` |
| 4.1.4 | `tools/samples_audit.py`: полный аудит лицензий → отчёт в `release/licenses.txt` |

#### 4.2 Грув и ритм
| ID | Задача |
|---|---|
| 4.2.1 | Паттерны для **120 жанров** в JSON (kick/snare/hat/808/melody, 16/32 шага, velocity-карты) вместо 3 захардкоженных |
| 4.2.2 | Humanize: микротайминг ±3–8 мс, velocity ±12 %, swing по жанру, ghost-ноты, late/early по инструментам |
| 4.2.3 | Грув из референса (`groove_extractor`): реальные смещения из аудио → применение к паттерну |
| 4.2.4 | Динамика секций: fill, stop-time, riser, drop-контраст ≥ 6 дБ по низу |

#### 4.3 Аранжировка
| ID | Задача |
|---|---|
| 4.3.1 | Энергетическая кривая трека (intro→build→drop→verse→chorus→bridge→outro), целевая длина 2:30–3:30 |
| 4.3.2 | «Хук за 15 секунд»: правило TikTok-входа, повторяемость мотива |
| 4.3.3 | Контроль плотности: не более N одновременных слоёв в секции (анти-каша) |

#### 4.4 Вокал
| ID | Задача |
|---|---|
| 4.4.1 | **Путь А (главный):** запись своего голоса — тюн (мягкий), де-эссер, чистка, громкость по фразам, дабл, ad-libs, дыхание |
| 4.4.2 | **Путь Б:** TTS/Silero/XTTS + RVC — с обязательным `FALLBACK`-маркером и гейтом на «пластик» |
| 4.4.3 | Просодия: паузы, ударения, длина фраз под сетку (сейчас — ровное чтение текста) |
| 4.4.4 | Бэкинг-вокал и хармони (существующий `female_backing` переписать на реальный pitch-shift) |

#### 4.5 Микс
| ID | Задача |
|---|---|
| 4.5.1 | Gain staging до -18 dBFS RMS на шине, headroom |
| 4.5.2 | Канальные EQ/компрессия, реверб/делэй сенды, сайдчейн kick↔808/bass |
| 4.5.3 | Панорама и стерео-ширина (mid/side, а не Haas) |
| 4.5.4 | Референс-матчинг микса (matchering/adapter) с отчётом отклонений |

#### 4.6 Мастеринг
| ID | Задача |
|---|---|
| 4.6.1 | Цепочка: коррекция тона → многополосная компрессия → лимитер → true-peak −1 dBTP |
| 4.6.2 | Целевые LUFS по стендам (−8…−9 клуб/тачка, −14 streaming), inter-sample peak-check |
| 4.6.3 | Проверка mono-совместимости и клиппинга на всех 8 стендах |

#### 4.7 «Не-ИИ» (anti-neuro)
| ID | Задача |
|---|---|
| 4.7.1 | Микро-вариативность каждого повтора (не 4 одинаковых бара) |
| 4.7.2 | «Человеческие» шероховатости: шум комнаты, дыхание, лёгкий дрейф темпа ±0.2 % |
| 4.7.3 | Тест «формульности»: entropy-метрика повторов ≥ порога |

**Приёмка этапа 4:** 5 демо-треков (phonk, drill, house, techno, pop) — все гейты §7.2
зелёные, слепое прослушивание пройдено, ни одного `BLOCKED` в релизном прогоне.

---

### Этап 5. UX и Windows 11 (5 дней)

| ID | Задача | Приёмка |
|---|---|---|
| 5.1 | `scripts/run.cmd` — один клик: venv → зависимости → GUI | свежая машина → трек без ручных шагов |
| 5.2 | Визард: 9 шагов → 5 (жанр+тема → референсы/пресет → голос → тонкая настройка → запуск) | прохождение за ≤ 60 с |
| 5.3 | Прогресс по стадиям, превью бита на 8-м такте, «пересобрать только вокал/мастер» | кнопки работают через кэш стадий |
| 5.4 | Тёмная тема, единый стиль, i18n ru/en для всего UI (1 518 строк → ключи) | ни одной строки мимо словаря |
| 5.5 | Устойчивость: без консоли, лог в `%LOCALAPPDATA%`, крэш-репорт, таймауты | закрытие окна не оставляет процессов |
| 5.6 | Упаковка: PyInstaller onefile с данными (`data/genres`, `data/prompts`, `data/samples`), `--version` smoke | EXE < 300 МБ, старт < 5 с |
| 5.7 | Установщик/портативный режим + инструкция | `INSTALL.md` проверен на чистой машине |

---

### Этап 6. Тесты и надёжность (3 дня, параллельно с 4)

| ID | Задача |
|---|---|
| 6.1 | Пирамида: unit ~70, audio ~25, e2e ~10, gui ~5. 312 «observability»-тестов свести к ~120 осмысленных |
| 6.2 | Аудио-фикстуры: 3 golden WAV (есть) + эталонные метрики; тест «seed → тот же WAV» |
| 6.3 | Property-based DSP-тесты (NaN/Inf, клиппинг, mono/stereo, длина) |
| 6.4 | e2e на Windows-раннере: полный прогон в `dry_run=False` на CPU, проверка артефактов |
| 6.5 | Покрытие: `pytest --cov` ≥ 70 % для `app/audio`, `app/pipeline`, `app/release` |
| 6.6 | Аудит «честности»: `tools/audit.py` — ноль `except: pass`, ноль `fake/simulate` в проде |

---

### Этап 7. Документация и управление (2 дня)

| ID | Задача |
|---|---|
| 7.1 | 4 документа: `README.md` (что/как), `docs/ARCHITECTURE.md` (слои, стадии, контракты), `docs/WORKFLOW.md` (как добавить стадию/жанр/сэмпл), `CHANGELOG.md` |
| 7.2 | `PROJECT_STATE.md` генерируется `tools/metrics.py` (матрица модулей/тестов/статусов) |
| 7.3 | `docs/history/` — сжатая история v1…v40 (индекс + ключевые решения), без дампов |
| 7.4 | ADR-практика: `docs/adr/NNN-*.md` для архитектурных решений |

---

### Этап 8. Релиз v41 (2 дня)

| ID | Задача |
|---|---|
| 8.1 | SemVer `41.0.0`, тег, GitHub Release с EXE + SHA-256 |
| 8.2 | Release preflight: версия/документы/лицензии/данные/тесты — всё автоматически |
| 8.3 | Проверка на чистой Windows 11 (без Python) |
| 8.4 | Offline-набор моделей (опционально): инструкция, контрольные суммы, `--ai-pull` |

---

### Этап 9. После v41 (backlog)

- Полностью нейро-бит (локальный MusicGen/small) как опция качества.
- Локальная LLM для текстов (Qwen 14B) с честным quality-gate.
- Слепой A/B против референс-плейлиста, автоматическая «хит-оценка» v2.
- Экспорт в DAW (stems + MIDI + проект), плагины VST.
- Автоматический релиз-конвейер (дистрибуция, обложки под площадки).

---

## 5a. Прогресс (обновляется по факту)

| Этап | Статус | Итог |
|---|---|---|
| 0. Гигиена репозитория | **готово** | 1657 → 320 файлов, `docs/` без дампов, `tools/readiness.py` переписан, версии синхронизированы (`41.0.0-alpha.1`) |
| 1. Удаление мусора и legacy | **готово** | удалены `orchestrator_v8..v12_patch`, `master_pipeline_v12`, 15 мёртвых модулей, все `*_vN.py`; состояние пользователя убрано из git |
| 2. Семантическое слияние дублей | **готово** | `lyrics_gen` (v7+v8+AI), мастеринг (6 → 3 модуля), `anti_neuro` + `anti_neuro_track`, пакет `modules/release/`, удалён `mixdown`; `app/pipeline/` с `StageStatus`/`StageResult`/`summarize`, `orchestrator.py` 2132 → 387, `orchestrator_ai.py` 668 → 129, стадии — `app/core/stages/*` и `app/core/ai/*` |
| 3. Единый пайплайн и стадии | **почти готово** | сделано: `beat_constructor` → `modules/beat/`, `app/gui/wizard` → `app/gui/wizard/`, `llm` → `modules/llm/`, `lyrics_gen` → `modules/lyrics/`, `hit_scorer` → `modules/hit_scorer/`, `main.py` 592 → 111 (`app/cli/`), `updater` → 6 модулей, `artist_dossier/manager` 539 → 380, стадийный рантайм вынесен в `app/core/pipeline_runtime.py` + `app/core/stages/vocal_chain.py`, `orchestrator` 387 → 339; добавлены детерминизм и частичные прогоны (`--seed`, `--resume`, `--only`, `--run`, `--list-stages`) с гейтом одинакового SHA-256; сделано: `rvc_manager` → `config/backend/trainer/infer`, `video_edit` → `models/audio/lrc/render/edits`, `voice_recording` → `state/recorder/takes/capability`, `kpi_dashboard` → `config/models/sources/checklist/report`, `vocal_fx` → `dsp/double/throw/pipeline`, `sample_hunter` → `config/planner/local/web/license/hunter`, `readiness` → пакет `tools/readiness/`; **файлов > 400 строк не осталось**; осталось: свести `orchestrator_god` (241) и `orchestrator_async` (118) к адаптерам над общим DAG |
| 4. Аудио-качество (сэмплы, грув, драматургия, микс, мастеринг, anti-neuro) | **почти готово (≈96 %)** | сделано: `modules/beat/drums.py` — физически осмысленный FALLBACK-синтез (питч-конверт кика + клик битера, две моды корпуса снейра + шум 1.4–11 кГц, клэп из 4 хлопков, 808-хэт из 6 негармонических прямоугольников, 808-бас с глиссандо, импакт дропа) и `modules/beat/humanize.py` — микротайминг ±9 мс по инструментам, velocity ±12 %, ghost-ноты, round-robin, сбивки; измерено на рендере 15 с: crest 17.3 дБ (бит) / 10.3 дБ (мастер), мастер peak −2.85 dBFS, RMS −13.1 dBFS; `modules/beat/harmony.py` — диатоника, прогрессии по жанрам, голосоведение ≤5 полутонов, пэд + FM-стабы (середина 17.7 → 20.2 %, крест 13.4 дБ), дроп 300 мс по кривой 4-й степени, убрана покадровая «pump»-нормализация; гейты в `tests/test_beat_humanize_and_drums.py` и `tests/test_beat_harmony.py`; сделано: 4.1.1–4.1.4 сэмпловый банк (`app/audio/samples.py`, `data/samples/manifest.json`, `tools/samples_audit.py`, фильтр лицензий CC0/CC-BY, velocity-слои, round-robin, аудит и `licenses.txt`), 4.2.1 ритмические семейства (15 семейств × 5 слотов × velocity-карты; все 50 жанровых пресетов спроецированы по ключевым словам); сделано: 4.2.2 humanize (микротайминг ±9 мс, velocity ±12 %, ghost-ноты, round-robin, сбивки), 4.2.3 грув из референса (измеренные атаки с шагом 1 мс, `timing_offsets_ms` + `timing_confidence`, перенос в бит с точностью ±4 мс), 4.2.4 контраст дропа (саб-хвост кика, саб-слой, сплит низа <120 Гц: измерено 6.7–7.6 дБ), 4.3 драматургия (`plan_sections` 2:30–3:30, энергия секций и гейны, потолок плотности 3/5/7, мотив хука в интро = правило TikTok); осталось: наполнить банк реальными CC0-сэмплами (код и аудит готовы) и 5 демо для слепого прослушивания; сделано: 4.5 микс — пакет `modules/mix` (gain staging −18 dBFS по опорному участку с потолком −3 dBFS, канальный EQ вокала HP80 + присутствие 3 кГц, сайдчейн kick → низ шины только <120 Гц, mid/side ширина с коридором корреляции 0.2…0.8, контроль крest-фактора, `mix_report.json`; измерено на прогоне seed 11: опорный RMS −18.0 dBFS, crest 12.1 дБ, корреляция 0.66, true peak −4.88 dBTP, 0 клиппов, 5/5 гейтов), 4.6 мастеринг — один движок `modules/mastering` (тон → двухполосная компрессия → мягкий клиппер → look-ahead лимитер −1 dBTP → сходимость по LUFS, калибровка на громком фрагменте), цели streaming −14 ± 0.5 / club −8.5 / car −10 / tiktok −11.5, отчёт `mastering_report.json` с гейтами по 8 стендам; измерено 8/8 зелёных (club −8.50 LUFS при crest 4.45), единый измерительный слой `modules/dsp` (true-peak 4×, LUFS BS.1770, crest, корреляция, потеря в моно), `mastering_chain` стал тонким адаптером; сделано: 4.7 anti-neuro (микро-вариация повторов 4.7.1, дрейф темпа ±0.2 % и шум комнаты −62 dBFS 4.7.2, энтропия типов тактов 4.7.3 — измерено 0.65 нормированной, 8 типов, formulaic=False) и 4.5.4 референс-матчинг микса с отчётом отклонений до/после (гейт 2.5 дБ), плюс аудит честности 6.6 (54 немых except зачищены, tools/audit_honesty.py в гейте); сделано: 4.4 вокальная цепочка (4.4.1 тюн фазовым вокодером с адаптивной силой — 0 → 99.7 % кадров в тоне, отклонение 65 → 0.8 цента; 4.4.2 динамический де-эссер по доле полосы — −5.4 дБ на шипящих, гласные без изменений; 4.4.3 просодия — уровни фраз ±6 дБ, дыхание −24 дБ, атаки к сетке ≤30 мс; 4.4.4 даблы и throw уже были), мастеринг 8/8 стендов зелёные при соблюдении crest-коридора (клуб −8.5 LUFS / crest 6.6, bluetooth −14.5 / 13.7, TP везде ≤ −1.0); осталось: наполнить банк реальными CC0-сэмплами и 5 демо для слепого прослушивания |
| 5. Вокал: свой микрофон как основной путь | не начато | — |
| 6. Мастер-гейты и слепое прослушивание | не начато | — |
| 7. Windows 11 one-click | частично | `scripts/setup.cmd`, `run.cmd`, `verify.cmd`, `make_shortcut.ps1` на месте, проверка на Windows впереди |

## 6. Списки на удаление (черновик, уточняется в Этапе 1–2)

**Без статических ссылок (26):** `agents/training_texts.py`, `app/core/cover_gen.py`,
`app/core/model_manager.py`, `app/gui/wizard_v8_extensions.py`, `modules/beat_gen.py`,
`modules/distribution.py`, `modules/expert_mode.py`,
`modules/phonk_engine_v2.py`, `modules/wizard_v12_integration.py`, `tools/ab_compare.py`,
`tools/cli.py`, `tools/deep_audit_v40*.py` (3), `tools/lazy_dirs_patch.py`,
`tools/p0_truth_test.py`, `tools/populate_cover_prompts.py`, `tools/validate_final_track.py`,
`ui/karaoke_recorder.py`, `ui/tutorial.py`, `app/gui/theme.py`, `modules/provenance.py`,
`app/core/orchestrator_v9_patch.py`, `app/core/orchestrator_v10_patch.py` (+ 3 CLI-only:
`tools/smoke_audio.py`, `tools/smoke_god.py` остаются как CLI).

**Только тестовые ссылки (16):** `agents/trend_scout.py`, `modules/genre_expansion_100.py`,
`modules/global_audit_fixer.py`, `modules/kpi_monitor.py`, `modules/release_export.py`,
`modules/remix.py`, `modules/video_edit.py`, `tools/ast_dead_imports.py`,
`tools/audio_golden_metrics.py`, `tools/audit_data_inventory.py`, `tools/deep_audit_v40.py`,
`tools/generate_audio_goldens.py`, `tools/genre_validator.py`, `tools/plan_integrity.py`,
`tools/regress_v39.py`, `tools/release_preflight.py` — каждый получает решение:
в продукт (CLI/UI) или удаление вместе с тестом.

---

## 7. Критерии качества

### 7.1 Инженерные (жёсткие гейты CI)

- `compileall` = 0 ошибок; `pytest -q` = 100 % зелёный на Linux и Windows.
- Ноль модулей без статической ссылки; ноль `except: pass`; ноль дублей ответственности.
- Размер файла ≤ 400 строк; покрытие `app/audio|pipeline|release` ≥ 70 %.
- Детерминизм: `seed` → идентичный SHA-256 артефакта (кроме AI-стадий с явным флагом).

### 7.2 Аудио-гейты (объективные, автоматические)

| Метрика | Порог |
|---|---|
| True peak (все стенды) | ≤ −1.0 dBTP |
| LUFS streaming / club | −14 ± 0.5 / −8…−9 |
| Стерео-корреляция микса | 0.2 … 0.8 (не моно, не «развал») |
| Crest factor микса | 8 … 14 дБ |
| Drop-контраст (низ) | ≥ 6 дБ |
| Доля тишины/клиппинга | < 2 % / 0 сэмплов |
| `hit_scorer` | ≥ 70 / 100 |
| `ai_detector` (внутренний) | «human» |
| Повторяемость секций (entropy) | ≤ порог формульности |

### 7.3 Продуктовые

- Свежая Windows 11 → трек за ≤ 10 минут (CPU-only, baseline RX 580 / Xeon).
- Один клик, без консоли, без ручных pip-команд.
- Любая стадия объясняет отказ человеческим языком и предлагает, что установить.

---

## 8. Риски и контрмеры

| Риск | Контрмера |
|---|---|
| Сэмпловая база: лицензии/размер репозитория | git-LFS или отдельный архив, манифест с лицензиями, аудит в CI |
| «Звучит как ИИ» не лечится DSP | явный путь «свой голос» + референс-матчинг; честная метрика качества |
| Big-bang рефакторинг ломает всё | по одному семейству на коммит, зелёные тесты после каждого |
| Windows-специфика (пути, кодеки, ffmpeg) | отдельный Windows-CI + `scripts/check_env.cmd` |
| Тяжёлые модели не влезают в baseline | `BLOCKED` + fallback на DSP-путь, оба пути тестируются |
| Время: 30+ дней работы | этапы 1–3 дают «чистый фундамент» уже через неделю, этап 4 идёт инкрементально по слоям |

---

## 9. Оценка

| Этап | Дней |
|---|---:|
| 0. Инженерная база | 1 |
| 1. Расчистка | 2 |
| 2. Дедупликация | 5 |
| 3. Пайплайн/кэш | 4 |
| 4. Качество звука | 12 |
| 5. UX/Windows | 5 |
| 6. Тесты | 3 |
| 7. Документация | 2 |
| 8. Релиз | 2 |
| **Итого** | **36 рабочих дней** (~7–8 рабочих сессий агента, если идти подряд) |

---

## 10. Что нужно решить до старта

1. **Документация:** удалить дампы `docs/PLAN_v39/**` и 11-МБ `PLAN_v38` совсем или
   сжать в архив (`.tar.zst`, ~1 МБ) и оставить в `docs/archive/`?
2. **Legacy v8–v12:** удаляем полностью (проще, чище) или сохраняем один адаптер
   для обратной совместимости?
3. **Сэмплы:** есть ли у тебя свои/скачанные сэмпл-паки и референс-треки? Их лицензии
   решают, кладём ли базу в репозиторий или тянем при установке.
4. **Вокал:** основной сценарий — ты записываешь свой голос в микрофон, или ставка на
   TTS/RVC? От этого зависит приоритет внутри Этапа 4.
5. **Windows-машина:** есть ли возможность прогонять релизные прогоны на ней (нужен
   агент-скрипт `scripts/collect_report.cmd`, который соберёт логи/метрики в архив).
6. **Куда деть `PROJECT_STATE`/`SESSION_LOG`:** генерируемые отчёты вместо ручных файлов —
   согласен?

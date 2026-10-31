# CHANGELOG

> Актуальная версия: **41.0.0-alpha.4** (2026-10-31). План рефакторинга —
> `docs/PLAN_v41_MASTER.md`, состояние — `PROJECT_STATE.md`.
> История до v40 сохранена ниже как архив: удалённый `SESSION_LOG.md` больше не поддерживается.

## 41.0.0-alpha.4 — барабаны и человеческий грув (2026-10-31)

Первый шаг Этапа 4: бит перестаёт звучать как синтезатор из синусов.

- **`modules/beat/drums.py` — FALLBACK-синтез one-shot'ов.** Кик с питч-конвертом
  (165→49 Гц), кликом битера и сатурированным телом; снейр из двух мод корпуса
  (185/330 Гц) плюс шум 1.4–11 кГц; клэп из четырёх хлопков с разлётом 0–22 мс и
  «хвостом» зала; 808-хэт из шести негармонических прямоугольников (ФВЧ 6.8 кГц,
  закрытый и открытый); 808-бас с глиссандо и мягкой сатурацией; импакт дропа.
  `CAPABILITIES` честно помечает движок как `FALLBACK`, пока банк сэмплов пуст.
- **`modules/beat/humanize.py` — «человечность».** Микротайминг по инструментам
  (кик ±1.4 мс, снейр +2…7 мс, хэты −3…+2.4 мс), свинг на нечётных шестнадцатых,
  velocity ±12 % с акцентами на сильных долях, ghost-ноты, round-robin вариантов,
  сбивки в конце фразы. Удар больше не прибит к сетке гвоздями.
- **Баланс микса** (`INSTRUMENT_GAIN`), новые слоты `clap` и `open_hat` в банке
  сэмплов, `drum_engine` в результате сборки бита.
- **Гейты:** `tests/test_beat_humanize_and_drums.py` — спектр кика (≥48 % энергии
  ниже 120 Гц), яркость хэта (центроид ≥6 кГц), смещение ударов от сетки
  0.3–9.5 мс, крест 6–22 дБ, отсутствие клиппинга.
- **Измерено** на рендере 90 с: бит crest 17.3 дБ, мастер peak −2.85 dBFS,
  RMS −13.1 dBFS, crest 10.3 дБ, корреляция 0.79.
- `tests/fixtures/audio/golden_beat_15s.wav` перегенерирован под новый движок,
  пороги подписи обновлены (rms 0.140–0.170, центроид 5.8–7.2 кГц, peak ≤ 0.97).
- `tools/readiness.py` → пакет `tools/readiness/` (`paths/inventory/probes/scoring/cli`),
  запуск — `python -m tools.readiness`.

## 41.0.0-alpha.3 — единый пайплайн и контракт стадий (2026-10-31)

Второй шаг Этапа 2: «один пайплайн, один формат результата стадии».

- **Контракт стадий:** новый пакет `app/pipeline/` — `StageStatus`
  (`OK / FALLBACK / BLOCKED / FAILED`), `StageResult`, `classify()` и
  `summarize()`. Вердикт и процент считаются **только** там; второй экземпляр
  модели стадии в `app/core/pipeline_core.py` удалён, `AIStage`-отчёты
  (`app/ai/sequential_runner.py`) теперь тоже несут честный `status`.
- **Оркестратор разобран:** `app/core/orchestrator.py` 2132 → 387 строк.
  Реализации стадий — `app/core/stages/{prep,beat,texture,lyrics,vocal,mix,master,release}.py`
  (каждый ≤ 320 строк), рецепт — `app/core/recipe.py`, склейка осталась в
  оркестраторе.
- **AI-пайплайн разобран:** `app/core/orchestrator_ai.py` 668 → 129 строк
  (только проводка), стадии — `app/core/ai/stages_{meta,music,vocal,final}.py`,
  рендер — `app/core/ai/render.py`, состояние — `AIContext`.
- **Свой микрофон — основной вокальный путь:** `_run_vocal_chain` берёт
  `own_vocal_wav` пользователя первой веткой, синтез идёт только при его
  отсутствии, синтетический скаффолд без RVC в мастер по-прежнему не попадает.
- **Найденные и исправленные дефекты** (были скрыты монолитными файлами):
  `_stage_analyze`/`_stage_groove` всегда падали с `TypeError` (лишний
  `q_params`); god-режим возвращал `None` вместо честного BLOCKED и ронял
  пайплайн на вокале; релиз-пакет молча уходил в минимальный фоллбек из-за
  `NameError: HAS_PYDUB`; `render_xtts_vocal`/`render_rvc_vocal` теряли импорты
  валидаторов.
- **Тесты:** добавлен `tests/test_pipeline_stage_contract.py` (16 кейсов на
  статусы, вердикты и рецепт) — всего 301 тест; smoke_audio 6/6, smoke_god 8/8.

## 41.0.0-alpha.2 — семантическое слияние дублей (2026-10-31)

Этап 2 плана: «одна ответственность — один модуль». Удалены все оставшиеся
дубли, каждая цепочка существует ровно в одном месте.

- **Тексты:** `lyrics_gen_v8` и `lyrics_gen_ai` влиты в `modules/lyrics_gen.py`
  (604 строки) — три входа (`generate_lyrics`, `generate_lyrics_ai`,
  `generate_lyrics_v8`) с общим контрактом и обязательным сохранением строк
  пользователя.
- **Мастеринг (было 6 реализаций):**
  `mastering.py` — мастеринг под 8 стендов (numpy-DSP, честные LUFS-метрики);
  `mastering_chain.py` — pedalboard-чейн трека, ceiling −1 dBTP, RMS-фоллбек;
  `mastering_reference.py` — единственный адаптер Matchering (+`master_ai`).
  Удалены `mastering_pro`, `mastering_ai`, `matchering_master`.
- **Вокал / трек:** `anti_ai_polish` влит в `anti_neuro`; затем модуль разделён
  по ответственности — вокальная цепочка (`anti_neuro.py`) и «оживление»
  микса (`anti_neuro_track.py`). `_stage_polish` пробует трековую цепочку,
  затем вокальную, и лишь потом честно копирует мастер (`fallback_used`).
- **Релиз:** `release_pack_full` + `release_export` + `distribution` → пакет
  `modules/release/` (`assets`, `text`, `pack`, `export`, `channels`, `models`)
  с ленивым публичным API. Мёртвая ветка `release_pack_v13` и её тест убраны:
  стадия релиза = один движок + честный минимальный пакет.
- **Микс:** удалён `modules/mixdown.py` (дубль канонической стадии микса
  в оркестраторе).
- **Имена:** тесты и фикстуры без версионных суффиксов
  (`test_lyrics_gen_orchestration`, `test_health_collection`,
  `test_theme_apply_observability`, `data/sample_manifests/*_test_samples.json`).
- **Гейты:** 285 тестов, `smoke_audio` 6/6, `smoke_god` 8/8, AST dead imports
  0, `compileall` 0 ошибок; устаревшие имена модулей вычищены из
  `health`, `kpi_dashboard`, `readiness`.

## 41.0.0-alpha.1 — расчистка и дедупликация репозитория (2026-10-31)

- **Репозиторий:** 1657 → 320 файлов; `docs/` 52 МБ → 3 документа + план.
  Удалены сгенерированные дампы `docs/PLAN_v38_AI_MEGA.txt` (11 МБ),
  `docs/PLAN_v39/**` (1017 файлов, 37 МБ), `STEP_STATUS` (144), `LICENSES`, `WIKI`,
  `REGRESS_v39`, `PLAN_v39_EXEC_REPORT`, `SESSION_LOG.md`.
- **P0 фикс:** `tools/readiness.py` переписан — устранён `SyntaxError` (f-string
  с `\|`) на Python ≤ 3.11, который ломал `--readiness`, CI-шаг `compileall` и
  три тест-модуля. Отчёт о лицензиях/плане убран: он жил только ради удалённых документов.
- **Legacy вырезан:** удалены `app/core/orchestrator_v8..v12_patch.py` вместе с
  `master_pipeline_v12`, `wizard_v12_integration`, `release_pack_v9`, `mastering_v9`
  и CLI-флагами `--legacy-off/--legacy-report`. `_stage_polish` теперь одна
  каноническая ветка: `anti_neuro` → `anti_ai_polish` → честная копия.
- **Мёртвый код:** удалены 15 модулей без единой статической ссылки
  (`training_texts`, `cover_gen`, `model_manager`, `wizard_v8_extensions`, `beat_gen`,
  `phonk_engine_v2`, `musical_intelligence`, `genre_expansion_100`,
  `global_audit_fixer`, `provenance`, `ui/tutorial`, `ab_compare`, `lazy_dirs_patch`,
  `p0_truth_test`, `populate_cover_prompts`, `validate_final_track`, `plan_integrity`,
  `regress_v39`, `release_preflight`, `deep_audit_v40*`).
- **Имена без версий:** `*_vN.py` переименованы в канонические
  (`anti_neuro`, `llm`, `lyric_vault`, `voice_vault`, `rvc_trainer`, `tiktok_edit`,
  `video_edit`, `distribution`, `expert_mode`, `health`, `kpi_dashboard`, `kpi_monitor`,
  `self_diag`, `onboarding`, `theme`, `tools/e2e`, `tools/smoke_audio`, `tools/smoke_god`).
- **Данные и состояние:** пользовательское состояние убрано из git
  (`lyric_vault/*`, `voice_vault/*`, `data/hw_profile.json`, `data/tutorial_settings.json`,
  `training_texts/progress.json`, `data/kpi_history_seed`); `.gitignore` переписан на
  allowlist вместо глоба `*.json`.
- **Скрипты запуска:** 6 корневых bat/sh/ps1 сведены в `scripts/` (`setup.cmd`,
  `run.cmd`, `verify.cmd`, `make_shortcut.ps1`, `run.sh`).
- **Документация:** `README.md` переписан, добавлены `docs/ARCHITECTURE.md` и
  `docs/WORKFLOW.md`, `PROJECT_STATE.md` генерируется из `tools/readiness.py`.
- **Проверки:** `compileall` = 0 ошибок, `pytest tests/` = **287 passed**,
  `smoke_audio` = 6/6, `smoke_god` = 8/8, `--readiness` = 65 % (ограничения честные:
  нет `.pth` RVC, MusicGen/Demucs, микрофона в CI).


## v39.9.0 — финализация всех 100 primary шагов PLAN_v39

- **Приватность и offline-first:** KPI history сохраняет только allowlisted non-PII metrics; Freesound, GitHub-status и update URL calls требуют явного opt-in (`--online` или `network.online=true`).
- **Проверяемые runtime paths:** `--legacy-off` печатает compatibility matrix без импорта патчей; `--ai` отображает 12 real stage updates (duration/VRAM/status); классический CPU pipeline возвращает валидный `master_path` без Torch.
- **Поставка:** `python -m build` создаёт installable wheel с `zs-music-maker`; чистый venv выполняет установленный `--version`. Release preflight проверяет main, source-version mirror, console entrypoint и доступность source-implied tag.
- **Evidence:** execution report извлекает commit evidence for all primary headings; plan integrity verifies strict UTF-8, exact 001–100 headings and SHA-256. Final local acceptance completed with 237 pytest tests, compileall, AST audit and managed-data audit.
- **Ограничение:** MusicGen, SDXL, XTTS, RVC, Demucs, CLAP and LLM model runtime/weights are optional. Their absence is reported as BLOCKED/fallback; this release does not claim local heavy-model inference.


## v39.9 — PLAN_v39 ШАГИ 023–068 (AI pipeline, safety, release, docs)

- **AI pipeline:** роли, quality gates, dossier, lyrics/beat/vocal/cover/master adapters, secure manifest и deterministic fallbacks расширены последовательными контрактами и regression tests.
- **Операции:** очередь рендера, release fingerprints/ZIP, hit-score cache, explicit internal AI-risk heuristic, secure installer/update status/path redaction.
- **Supply chain:** model pull/verify сохраняет role-scoped artifacts и проверяет published checksums; data inventory остаётся 73 managed / 0 unknown / 0 invalid.
- **CI/CD:** Windows PyInstaller workflow сохраняет EXE artifact 30 дней; `v*` tag после успешной build публикует GitHub Release с ZIP.
- **Документация:** README/INSTALL/DEVELOPER_GUIDE синхронизированы с реальными v39 CLI contracts. На приёмке документации: 137 pytest PASS, AST dead-imports 0.
- **Ограничение:** runtime для тяжёлых optional packages и model weights остаётся environment-dependent и при отсутствии честно BLOCKED.


## v39.9 — PLAN_v39 ШАГИ 018–022 (metadata + audio quality gates)

- **ШАГ 018:** analysis_llm применяет общий schema-validator для трековых и агрегированных досье; неполные структуры фиксируются как честный rejected/deferred result.
- **ШАГИ 019–020:** metadata-стадия формирует и сохраняет валидный `metadata.json` даже без LLM, используя прозрачный deterministic fallback. Валидация проверяет title, описание и непустые теги.
- **ШАГИ 021–022:** добавлены метрики audio artifact (читаемость, длительность, sample rate, каналы, peak, RMS). И MusicGen, и CyberSynth fallback проходят gate до выставления `ok=True`; silent, missing и слишком короткий файл блокируются с reason.
- **Покрытие:** добавлены регрессии metadata-контракта, signal/silence audio quality и dry-run fallback; тяжёлые модели остаются BLOCKED до явного pull/install.


## v39.8 — PLAN_v39 ШАГИ 013–017 (data inventory + LLM quality)

- **ШАГ 013:** `tools/audit_data_inventory.py` читает и валидирует каждый versioned asset из `data/`; добавлены тесты чистого каталога и диагностики неизвестного/битого файла. Инвентарь: 73 managed, 0 unknown, 0 invalid.
- **ШАГ 014:** удалён устаревший reference-cache JSON, сохранён `.gitkeep`; `.gitignore` защищает локальные `reference_cache`, KPI/history, profile, secrets и API-key от случайного коммита. Сжатый архив HEAD — около 1.0 MB, tracked audio/model binaries отсутствуют.
- **ШАГИ 015–016:** `lyrics_llm` использует общий валидатор длины, токенов и повторяемости; invalid output запускает существующий fallback до записи `lyrics.txt`. Метрики прикладываются к результату стадии.
- **ШАГ 017:** output analysis_llm в artist dossier и track dossier проходит schema-валидацию; неполный JSON становится честным deferred/error результатом. Обе LLM-роли остаются BLOCKED без весов и `llama_cpp`, а не заявляются как установленные.


## v39.7 — PLAN_v39 ШАГ 012 (legacy isolation + God Mode checkpoints)

- **ШАГ 012:** добавлен `--legacy-off`, отключающий импорт и регистрацию legacy-патчей v8–v12 для runtime-пайплайнов без удаления совместимого Wizard-слоя.
- **Наблюдаемость legacy:** loader возвращает отчёт `enabled/loaded/skipped`; успешный вызов `anti_neuro` в core-оркестраторе получает `stage_marker=LEGACY`, а fallback сохраняет `legacy_attempt`.
- **FIX P0 God Mode:** `ZSPipeline` поддерживает явный `checkpoint_dir`. `run_god_pipeline()` изолирует checkpoints в собственном `out_root` и не переиспользует их для smoke/изолированных запусков. Устранён false-completed результат с отсутствующим `master_god.wav` после очистки out_root.
- **Покрытие:** добавлены четыре регрессионных теста — безимпортный legacy-off, CLI wiring, LEGACY marker и explicit checkpoint directory.
- **Приёмка:** 53 pytest PASS, AST dead-imports = 0, smoke_audio = 6/6, smoke_god = 8/8, `--legacy-off --smoke` = 8/8, fallback audit = 0 red flags.


## v39.6 — PLAN_v39 ШАГ 011 (import-cycle guard + audio regression)

- **ШАГ 011:** `tests/test_ai_layer.py` теперь строит статический AST-граф прямых импортов `app.core`, `modules` и `agents`, запрещая циклы с полным путём диагностики. Lazy-imports внутри функций намеренно исключены.
- **Регрессия детектора:** добавлен искусственный трёхузловой цикл, подтверждающий корректность обнаружения; фактический граф проекта — 104 модуля, 18 рёбер, 0 циклов.
- **FIX P0 audio:** `modules/beat_constructor.py` заменяет односторонний Haas-mix на контролируемое mid/side-расширение. Исправлен реальный `smoke_audio` fail: beat correlation 0.842, проверка 6/6 PASS.
- **Покрытие:** добавлен детерминированный тест стереоширины конструктора бита; тест проверки `essentia` больше не зависит от случайного состава необязательных локальных пакетов.
- **Приёмка:** 49 pytest PASS, AST dead-imports = 0, smoke_audio = 6/6, smoke_god = 8/8, fallback audit = 0 red flags.


## v39.5 — PLAN_v39 ШАГИ 006-010 (deps, config, CI, version, AST)

- ШАГ 006: requirements выверены по AST-графу импортов; +cryptography, audiomentations, moviepy(<2), noisereduce, lyricsgenius, mingus; AI-стек +essentia, pyAudioAnalysis, bark(git), rvc-python; pyproject deps синхронизированы, добавлен [project.optional-dependencies.ai].
- ШАГ 007: config/settings.py — единые настройки (.env → env → дефолты), подключены в main.py --version и orchestrator_ai.
- ШАГ 008: CI +job audit (compileall, AST dead-imports, pytest, --version).
- ШАГ 009: version.json — единственный источник версии; pyproject dynamic через app/version_info.py; тест сверки.
- ШАГ 010: tools/ast_dead_imports.py + чистка: musical_intelligence, orchestrator_god, genre_validator, test_ai_layer, ui/__init__; аудит = 0.

## v36 — 2026-08-14 (session-docs-unification-silent-except-build-fixes)

- **FIX P1 README/CHANGELOG unification** — вычищены протухшие блоки «Что нового в v14/v17/v18», ссылки на удалённые smoke_v14/v15/v17/v18/v21/v24/v25 (перенесены в `docs/legacy/` ещё в v29). Таблица статусов и раздел «Тесты» приведены к текущему v35+ ядру.
- **FIX P1 `main.py --smoke`** — fallback-цепочка чистилась от мёртвых имён (`tools.smoke_v14/v15/v17/v21/v24/v25`). Оставлены только реально работающие `tools.smoke_god` → `tools.smoke_audio`. Больше не спамит 6 строк «failed: No module named».
- **FIX P2 silent-except в критичных путях:**
  - `app/plugins/base.py:48` — `except: pass` внутри Sanitize-warning: теперь честно логирует в stderr, если `app_logger` недоступен.
  - `app/core/cover_gen.py:39` — `except: continue` в font-loop разделён на штатный `OSError` (шумовое отсутствие шрифта) и общий `Exception` с записью в stderr.
- **FIX P1 `.github/workflows/build.yml` (PyInstaller EXE)** — добавлены `--add-data models`, `--collect-submodules modules|app|agents|tools|ui|updater` вместо мёртвого `--hidden-import modules`. Smoke-шаг больше НЕ `continue-on-error: true` — падение EXE теперь ломает сборку (раньше «зелёная» сборка выпускала мёртвый EXE).
- **Cleanup `requirements.txt`** — убран устаревший заголовок «v10 Chart Killer Pro» и упоминание несуществующего `windows_build.bat`. Опциональные тяжёлые пакеты вынесены отдельной секцией с указанием на INSTALL.md §4.
- **Docs sync** — `INSTALL.md`, `PROJECT_STATE.md`, `version.json`, `pyproject.toml` подняты до v36.0.0.

## v35 — 2026-08-14 (session-silero-real-musicgen-status-cleanup)

- **REAL_PASS: `voice_synth` Silero TTS** — впервые подтверждён реальным прогоном на CPU (RU v3.1, female=kseniya, WAV 48kHz/6.7s живой сигнал). Статус снят с FALLBACK_ONLY.
- **FIX P1: `musicgen_texture`** — добавлен honest `detect_availability()`/`get_status()` (проверка torch+audiocraft БЕЗ загрузки весов) вместо молчаливого падения в лог; лог причины BLOCKED на вызове.
- **FIX P2: точечная честность silent except** — `master_pipeline_v12` (log-write/progress_cb/hit_scorer) и `release_pack_full` (ID3-обложка) больше не проглатывают ошибки молча — честно логируют в stderr/лог.
- **Cleanup:** удалён мёртвый `safe_import.py` (0 продакт-импортов); из git-индекса убраны чужие снапшоты `data/health.json`/`data/kpi_dashboard.json`; `tutorial_settings.json` перенесён в `data/` (дубль после миграции v34).
- **FIX INSTALL.md:** зафиксирована согласованная пара `torch==2.5.1`+`torchaudio==2.5.1` с pytorch-индекса (реальный ABI-баг: PyPI-torchaudio несовместим с torch pytorch-индекса → `_torchaudio.abi3.so` не грузится) + проверенный Silero-путь (`omegaconf soundfile`).

## v34 — 2026-08-13 (session-backlog-fixes)

- FIX P2: `app/core/model_manager` — lazy torch import (core-слой больше не падает без torch).
- FIX P2: license-gate реально подключён к `sample_hunter_v9.search_online()` + нормализация URL-лицензий в `license_manager`.
- FIX P3: `voice_onboarding.run_cli()` возвращает 0/1 по capability микрофона.
- FIX P3: `tutorial_settings.json` — единый путь `data/tutorial_settings.json` для `onboarding` и `ui/tutorial`.
- FIX P3: `voice_synth.synth(gender=...)` (male=aidar / female=kseniya).
- FIX P2: `_json_safe()` в `orchestrator_god.meta` (numpy-скаляры больше не превращаются в `np.float32(0.95)` строки).
- FIX main.py: валидация `--genre` против StyleRegistry с difflib-подсказкой (rc=2 + suggest).
- Docs sync: version 34.0.0 в version.json/pyproject/README/PROJECT_STATE.
- `.env.example` создан на основе реального сканирования кода.

## v33 — 2026-08-13 (session-full-pass)

- FIX P0: `run_all_smoke.bat` (4 несуществующих smoke) → прогон `tools/smoke_v*.py`.
- FIX P0: `voice_synth` уникализация draft-имени timestamp'ом (нет коллизий).
- FIX P0: `orchestrator_god` больше не режет вокал до 200 символов (safety-cap 4000).
- FIX P0: INSTALL.md переписан (убраны ссылки на несуществующий windows_build.bat, gradio-порт).
- FIX P1: unification версий 33.0.0 (version.json / pyproject / README / PROJECT_STATE).
- FIX P1: numpy пин `<2.0` снят (совместимость с 2.4.x подтверждена).
- FIX P1: `install.py` — `shell=True` убран.
- FIX P1: `async-mode` возвращает 1 при падении пайплайна.
- FIX P1: CI прогоняет smoke_audio + smoke_god + fallback_audit + CLI-sanity (раньше только 7 pytest).
- FIX P1: launcher cleanup (удалены дубли run_v8/v9/v11.bat и run_v14.sh в docs/legacy/).
- NEW: `tools/fallback_audit.py` теперь ловит многострочные вызовы с маркером `ZSMM_NOT_RVC` (red_flags=0).

## v30–v32 — audit + restore + God Mode E2E

- v30: восстановлены 5 ошибочно удалённых модулей (lyrics_gen_v8, mastering_v9, release_pack_v9, kpi_monitor, lyric_vault); `voice_synth` honest-empty-return; создан `run.bat`; `verify.bat` переписан на реальные тесты.
- v31/v32: два глубоких аудита без правок — 46 находок в SESSION_LOG (INSTALL.md битый, health-RED из-за опциональных heavy-deps, рассинхрон версий, ложные red-флаги, архитектурный распад оркестраторов).

## v29 — God Mode E2E + true-peak mastering

- FIX P0: `midi_generator.generate_melody_pattern` guard без mido (honest BLOCKED).
- FIX P1: `mastering_pro` true-peak -1 dBTP, NaN/Inf-guard, mono→stereo, honest output metrics.
- NEW: `tools/smoke_god.py` (God Mode E2E → master_god.wav) 8/8 PASS.
- Cleanup: 11 устаревших smoke → docs/legacy/.

## v28 — cleanup + God Mode wizard fix + CI

- Репо очищено от 72 output-артефактов (~262MB), `.gitignore` расширен.
- God Mode `wizard_state=None` защищён Optional + default.
- Добавлен `.github/workflows/build.yml` (Windows EXE, PyInstaller).
- Создан SESSION_LOG.md.

## v27 и раньше

Полная история — в `SESSION_LOG.md` (архивная секция).

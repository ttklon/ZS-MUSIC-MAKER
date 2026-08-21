# CHANGELOG

> Актуальная версия: **v36.0.0** (2026-08-14). Полная история сессий v10–v35 — в `SESSION_LOG.md`.


## v39.5 — PLAN_v39 ШАГИ 006-010 (deps, config, CI, version, AST)

- ШАГ 006: requirements выверены по AST-графу импортов; +cryptography, audiomentations, moviepy(<2), noisereduce, lyricsgenius, mingus; AI-стек +essentia, pyAudioAnalysis, bark(git), rvc-python; pyproject deps синхронизированы, добавлен [project.optional-dependencies.ai].
- ШАГ 007: config/settings.py — единые настройки (.env → env → дефолты), подключены в main.py --version и orchestrator_ai.
- ШАГ 008: CI +job audit (compileall, AST dead-imports, pytest, --version).
- ШАГ 009: version.json — единственный источник версии; pyproject dynamic через app/version_info.py; тест сверки.
- ШАГ 010: tools/ast_dead_imports.py + чистка: musical_intelligence, orchestrator_god, genre_validator, test_ai_layer, ui/__init__; аудит = 0.

## v36 — 2026-08-14 (session-docs-unification-silent-except-build-fixes)

- **FIX P1 README/CHANGELOG unification** — вычищены протухшие блоки «Что нового в v14/v17/v18», ссылки на удалённые smoke_v14/v15/v17/v18/v21/v24/v25 (перенесены в `docs/legacy/` ещё в v29). Таблица статусов и раздел «Тесты» приведены к текущему v35+ ядру.
- **FIX P1 `main.py --smoke`** — fallback-цепочка чистилась от мёртвых имён (`tools.smoke_v14/v15/v17/v21/v24/v25`). Оставлены только реально работающие `tools.smoke_v29` → `tools.smoke_v26`. Больше не спамит 6 строк «failed: No module named».
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
- **Cleanup:** удалён мёртвый `safe_import.py` (0 продакт-импортов); из git-индекса убраны чужие снапшоты `data/health_v12.json`/`data/kpi_dashboard_v12.json`; `tutorial_settings.json` перенесён в `data/` (дубль после миграции v34).
- **FIX INSTALL.md:** зафиксирована согласованная пара `torch==2.5.1`+`torchaudio==2.5.1` с pytorch-индекса (реальный ABI-баг: PyPI-torchaudio несовместим с torch pytorch-индекса → `_torchaudio.abi3.so` не грузится) + проверенный Silero-путь (`omegaconf soundfile`).

## v34 — 2026-08-13 (session-backlog-fixes)

- FIX P2: `app/core/model_manager` — lazy torch import (core-слой больше не падает без torch).
- FIX P2: license-gate реально подключён к `sample_hunter_v9.search_online()` + нормализация URL-лицензий в `license_manager`.
- FIX P3: `voice_onboarding.run_cli()` возвращает 0/1 по capability микрофона.
- FIX P3: `tutorial_settings.json` — единый путь `data/tutorial_settings.json` для `onboarding_tour` и `ui/tutorial`.
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
- FIX P1: CI прогоняет smoke_v26 + smoke_v29 + fallback_audit + CLI-sanity (раньше только 7 pytest).
- FIX P1: launcher cleanup (удалены дубли run_v8/v9/v11.bat и run_v14.sh в docs/legacy/).
- NEW: `tools/fallback_audit.py` теперь ловит многострочные вызовы с маркером `ZSMM_NOT_RVC` (red_flags=0).

## v30–v32 — audit + restore + God Mode E2E

- v30: восстановлены 5 ошибочно удалённых модулей (lyrics_gen_v8, mastering_v9, release_pack_v9, hit_kpi_monitor_v11, lyric_vault_v10); `voice_synth` honest-empty-return; создан `run.bat`; `verify.bat` переписан на реальные тесты.
- v31/v32: два глубоких аудита без правок — 46 находок в SESSION_LOG (INSTALL.md битый, health-RED из-за опциональных heavy-deps, рассинхрон версий, ложные red-флаги, архитектурный распад оркестраторов).

## v29 — God Mode E2E + true-peak mastering

- FIX P0: `midi_generator.generate_melody_pattern` guard без mido (honest BLOCKED).
- FIX P1: `mastering_pro` true-peak -1 dBTP, NaN/Inf-guard, mono→stereo, honest output metrics.
- NEW: `tools/smoke_v29.py` (God Mode E2E → master_god.wav) 8/8 PASS.
- Cleanup: 11 устаревших smoke → docs/legacy/.

## v28 — cleanup + God Mode wizard fix + CI

- Репо очищено от 72 output-артефактов (~262MB), `.gitignore` расширен.
- God Mode `wizard_state=None` защищён Optional + default.
- Добавлен `.github/workflows/build.yml` (Windows EXE, PyInstaller).
- Создан SESSION_LOG.md.

## v27 и раньше

Полная история — в `SESSION_LOG.md` (архивная секция).

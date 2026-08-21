
---

## КОММИТ v39.4 — PLAN_v39 ШАГИ 001-005 (исполнены)

| Шаг | Что сделано | Файлы |
|---|---|---|
| 001 | Dead-imports удалены (typing/pickle/os/logging/hashlib/safe_hash/random/json/torch_directml-attempt/agents re-export) | orchestrator_ai/god/async, pipeline_core, logger, model_manager, cover_gen, genre_engine, genre_expansion_100, global_audit_fixer, midi_generator, lyrics_gen_ai, ai_arranger, agents/__init__ |
| 002 | Hardcoded `C:\Windows\Fonts` и `/usr/share/fonts/...` вынесены в единый `app/core/font_utils.py` (env-override `ZSMM_FONT_PATH`, `config/fonts.txt`, cross-OS кандидаты) | +font_utils.py, cover_gen, cover_art_gen, video_edit_v11 |
| 003 | Реальный ISRC (ISO 3901 `CC-XXX-YY-NNNNN`) вместо заглушки `XX-XXX-00-00000`; генератор+валидатор+детектор placeholder | +app/core/isrc.py, release_pack_full, release_export, distribution_export_v11 |
| 004 | Единый формат логов стадий `stage=X event=Y duration_ms=N`; хелпер `log_stage` в app_logger | logger.py, pipeline_core.py |
| 005 | Silent `except: pass` → честные логи (orchestrator_ai.stage_lyrics fallback, plugins/base.discover) | orchestrator_ai.py, plugins/base.py |

Проверка: `compileall` OK, `pytest tests/` = **30/30 PASS** (+14 новых: test_isrc, test_font_utils), `main.py --help/--version` OK. Версия: 39.4.0.


---

## КОММИТ v39.5 — PLAN_v39 ШАГИ 006-010 (исполнены)

| Шаг | Что сделано | Файлы |
|---|---|---|
| 006 | requirements выверены AST-аудитом: +cryptography/audiomentations/moviepy/noisereduce/lyricsgenius/mingus (база), +essentia/pyAudioAnalysis/bark/rvc-python (AI); pyproject синхронизирован + optional-deps ai | requirements.txt, requirements_ai.txt, pyproject.toml |
| 007 | config/settings.py — единый загрузчик (.env → env → дефолты), dump(); main.py --version показывает config_path; orchestrator_ai логирует конфиг и кладёт в результат | +config/settings.py, +config/__init__.py, main.py, orchestrator_ai.py |
| 008 | ci.yml +job audit: compileall + AST-dead-imports + pytest + --version | .github/workflows/ci.yml |
| 009 | version.json — единственный источник; pyproject dynamic version через app/version_info.py; тесты сверки | +app/version_info.py, pyproject.toml, +tests/test_version_consistency.py |
| 010 | tools/ast_dead_imports.py — повторный аудит = 0: musical_intelligence (sf/aT/audioBasicIO/ShortTermFeatures), orchestrator_god (app_logger), genre_validator (os), test_ai_layer (os), ui/__init__ (re-exports) | +tools/ast_dead_imports.py, 5 файлов, +tests/test_ast_dead_imports.py |

Проверка: compileall OK, AST-аудит = 0 dead-imports, pytest = **41 PASS**, main.py --version/--help OK. Версия: 39.5.0.

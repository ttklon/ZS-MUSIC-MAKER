
---

## КОММИТ — PLAN_v39 ШАГ 033: CLAP audio_tagger integration (выполнен, runtime BLOCKED)

Dossier CLAP-stage теперь явно обрабатывает отсутствующий bundle и ранжирует `logits_per_audio` через `rank_clap_tags()` с проверкой соответствия score-vector фиксированному словарю кандидатов. Ошибка размерности или runtime не выдаёт произвольные tags.

Проверка: top-N соответствует logits; mismatch scores/vocabulary отклоняется. `pytest tests/` = **82/82 PASS**; compileall OK; AST dead-imports = **0**. CLAP/weights не установлены. Детали: `docs/STEP_STATUS/033_clap_integration.md`.

---

## КОММИТ — PLAN_v39 ШАГ 032: ASR quality и fallback (выполнен, runtime BLOCKED)

Добавлен `validate_asr_transcript()`: transcript оценивается по символам, токенам и unique ratio; пустой или зацикленный результат не сохраняется в dossier. При отклонении reference audio остаётся источником, а текст не подменяется фиктивным fallback.

Проверка: валидный transcript проходит; пустой и повторяющийся отклоняются; невалидный transcript не создаёт файл. `pytest tests/` = **80/80 PASS**; compileall OK; AST dead-imports = **0**. ASR runtime/weights отсутствуют. Детали: `docs/STEP_STATUS/032_asr_quality.md`.

---

## КОММИТ — PLAN_v39 ШАГ 031: faster-whisper ASR integration (выполнен, runtime BLOCKED)

ASR-вызов вынесен в `transcribe_reference_audio()`: handle получает `language=ru` и `beam_size=5`, сегменты объединяются и transcript сохраняется в dossier. При отсутствии ASR или audio возвращается explicit skipped, а runtime-error остаётся диагностируемым failure.

Проверка: fake ASR подтвердил параметры, transcript и UTF-8 файл; error-case подтверждает отсутствие ложного успеха. `pytest tests/` = **78/78 PASS**; compileall OK; AST dead-imports = **0**. `faster-whisper`/weights отсутствуют. Детали: `docs/STEP_STATUS/031_asr_integration.md`.

---

## КОММИТ — PLAN_v39 ШАГ 030: Demucs quality gate (выполнен, runtime BLOCKED)

Добавлен `validate_stem_artifact(original, stem)`: vocal stem проходит базовый audio gate и обязан сохранить 95–105% длительности входного трека до передачи в ASR. Silent, битые и усечённые stems теперь не выдаются за пригодные данные.

Проверка: 1-second stem проходит; 0.875-second stem отклоняется по duration ratio. `pytest tests/` = **76/76 PASS**; compileall OK; AST dead-imports = **0**. Demucs runtime/weights отсутствуют. Детали: `docs/STEP_STATUS/030_demucs_quality.md`.

---

## КОММИТ — PLAN_v39 ШАГ 029: Demucs htdemucs integration (выполнен, runtime BLOCKED)

Проверен существующий `stem_splitter` registry/pull route. В dossier Demucs теперь выбирает stem `vocals` по `model.sources`, а не по фиксированному индексу; отсутствие нужного source или runtime даёт явную диагностику/skipped. Создание output-папки гарантировано перед записью.

Проверка: model с нестандартным порядком sources даёт корректный vocal index; модель без `vocals` отклоняется. `pytest tests/` = **75/75 PASS**; compileall OK; AST dead-imports = **0**. Demucs runtime/weights не установлены. Детали: `docs/STEP_STATUS/029_demucs_integration.md`.

---

## КОММИТ — PLAN_v39 ШАГ 028: RVC quality gate (выполнен, runtime BLOCKED)

Добавлен `validate_rvc_artifact(input, output)`: RVC output обязан пройти базовый audio gate и сохранить 85–115% длительности исходного вокала. Несвязанный, silent или укороченный результат теперь не может пройти как готовая voice conversion; pitch-shift fallback по-прежнему запрещён.

Проверка: корректный 1-second RVC output проходит; 0.5-second output отклоняется по duration ratio. `pytest tests/` = **73/73 PASS**; compileall OK; AST dead-imports = **0**. RVC runtime/model отсутствуют. Детали: `docs/STEP_STATUS/028_rvc_quality.md`.

---

## КОММИТ — PLAN_v39 ШАГ 027: RVC v2 integration (выполнен, runtime BLOCKED)

Исправлена связь AI-оркестратора с RVC: вместо несуществующего `handle.convert` используется публичный `rvc_manager.infer(input_wav, voice_name, pitch_shift, out_name)`. Result переносится в `<project>/vocal_rvc.wav`; ошибки или отсутствие runtime/model дают честный failure/skipped. Pitch-shift не используется как подмена RVC.

Проверка: fake manager подтверждает аргументы `infer` и project artifact; runtime-error подтверждает отсутствие скрытого fallback. `pytest tests/` = **72/72 PASS**; compileall OK; AST dead-imports = **0**. `.pth` и `rvc-python` в sandbox отсутствуют, поэтому реальная conversion **не заявляется как выполненная**. Детали: `docs/STEP_STATUS/027_rvc_integration.md`.

---

## КОММИТ — PLAN_v39 ШАГ 026: XTTS-v2 quality и fallback (выполнен, runtime BLOCKED)

Добавлен `validate_vocal_artifact()`: gate связывает токены текста с минимальной длительностью, а также применяет readability/RMS/peak-проверки. Если XTTS недоступен или его файл отклонён, вызывается `voice_synth.synth(engine="auto")`; success возможен только для реально созданного и валидированного WAV. Отсутствие всех движков возвращает explicit failure, без фиктивного вокала.

Проверка: валидный WAV проходит; короткий relative-to-text WAV отклоняется; fallback копирует и валидирует audio; отсутствие движка честно падает. `pytest tests/` = **70/70 PASS**; compileall OK; AST dead-imports = **0**. XTTS runtime не установлен. Детали: `docs/STEP_STATUS/026_xtts_quality.md`.

---

## КОММИТ — PLAN_v39 ШАГ 025: XTTS-v2 integration (выполнен, runtime BLOCKED)

`stage_vocal` теперь вызывает изолированный `render_xtts_vocal()`: контракт включает `text`, `file_path`, `language=ru` и существующий `speaker_wav`; success требует созданный непустой аудиофайл. Fake XTTS подтвердил параметры и WAV, пустой output отклоняется без ложного успеха.

Проверка: `pytest tests/` = **67/67 PASS**; compileall OK; AST dead-imports = **0**. Coqui TTS/XTTS не установлены в sandbox, поэтому реальный voice render **не заявляется как выполненный**; optional stage продолжает возвращать explicit `skipped`. Детали: `docs/STEP_STATUS/025_xtts_integration.md`.

---

## КОММИТ — PLAN_v39 ШАГ 024: music_stereo quality gate (выполнен, runtime BLOCKED)

`audio_metrics()` дополнен `stereo_correlation` и `stereo_side_rms`; `validate_stereo_texture()` требует stereo-каналы, side RMS ≥ 0.0005 и `abs(correlation) ≤ 0.995`, помимо базовой проверки WAV. `stage_music_stereo` может вернуть `ok=True` только после этого gate. При отсутствии MusicGen fallback явный: основной beat сохраняется без поддельной текстуры.

Проверка: независимый stereo WAV проходит; продублированный mono WAV отклоняется; `pytest tests/` = **65/65 PASS**; compileall OK; AST dead-imports = **0**. Реальный `musicgen-stereo-medium` всё ещё не установлен, поэтому runtime status честно остаётся BLOCKED. Детали: `docs/STEP_STATUS/024_music_stereo_quality.md`.

---

## КОММИТ — PLAN_v39 ШАГ 023: music_stereo integration (выполнен, runtime BLOCKED)

Добавлена отдельная `AIStage("music_stereo", "music_stereo", ...)` после основной генерации. `render_stereo_texture()` использует только совместимый MusicGen handle (`set_generation_params` → `generate`), конвертирует tensor в stereo WAV и сохраняет `texture_stereo.wav` как независимый артефакт. Основной beat и mix пока не изменяются; это предотвращает скрытую аудиорегрессию до отдельной quality-приёмки ШАГА 024.

Проверка: fake-handle test подтверждает настоящий вызов контракта и stereo WAV; dry-run подтверждает присутствие стадии в runner; `pytest tests/` = **64/64 PASS**; compileall OK; AST dead-imports = **0**. `audiocraft`/веса отсутствуют в sandbox — реальная генерация **не заявляется как выполненная** и возвращает explicit `skipped` до установки на целевой машине. Детали: `docs/STEP_STATUS/023_music_stereo.md`.

---

## КОММИТ v39.9 — PLAN_v39 ШАГИ 018-022 (metadata + audio quality gates)

| Шаг | Что сделано | Файлы |
|---|---|---|
| 018 | Общий `validate_analysis_json` применяется к track и artist dossier; битой/неполной структуре не присваивается статус успешного AI-анализа. | `app/ai/quality.py`, `modules/artist_dossier/manager.py` |
| 019-020 | `stage_metadata` создаёт валидный JSON при dry-run, отсутствии LLM или ошибочном JSON. Контракт требует title, описание и tags; в output сохраняются `source`, `quality`, `reason`. | `app/core/orchestrator_ai.py`, `tests/test_ai_quality.py` |
| 021-022 | `audio_metrics` и `validate_audio_artifact` проверяют readability/duration/sample-rate/channels/peak/RMS. MusicGen и CyberSynth fallback могут вернуть `ok=True` только после quality gate. | `app/ai/quality.py`, `app/core/orchestrator_ai.py`, `tests/test_ai_quality.py` |

Проверка: `pytest tests/` = **62/62 PASS**; compileall OK; data audit = **73/73 managed**; AST dead-imports = **0**; `smoke_v26` = **6/6 PASS**; `smoke_v29` = **8/8 PASS**; fallback audit = **0 red flags**. Heavy weights (`metadata_llm`, MusicGen) не загружались и остаются **BLOCKED** до явной установки; fallback-paths теперь измеряемы и не маскируют silent/missing output. Версия: **39.9.0**.

---

## КОММИТ v39.8 — PLAN_v39 ШАГИ 013-017 (исполнены с честным BLOCKED heavy-ролей)

| Шаг | Что сделано | Файлы |
|---|---|---|
| 013 | Добавлен `tools/audit_data_inventory.py`: читает и валидирует каждый versioned data-asset, классифицирует lifecycle и возвращает non-zero при неизвестном или битом файле. Инвентарь: 73 managed, 0 unknown, 0 invalid. | `tools/audit_data_inventory.py`, `tests/test_data_inventory.py`, `data/README.md` |
| 014 | Удалён устаревший reference cache JSON; каталог сохраняется через `.gitkeep`. Runtime cache/history/profile/secrets дополнительно исключены `.gitignore`; в tracked tree нет audio/model binaries, сжатый архив ~1.0 MB. | `.gitignore`, `data/reference_cache/` |
| 015-016 | Создан `app/ai/quality.py` с метриками lyrics (длина, токены, unique ratio, повтор строк) и валидатором. `orchestrator_ai.stage_lyrics` теперь валидирует output LLM до сохранения и запускает fallback при пустом/коротком/зацикленном тексте. | `app/ai/quality.py`, `app/core/orchestrator_ai.py`, `tests/test_ai_layer.py` |
| 017 | Track/artist dossier analysis_llm использует schema-валидацию общего quality-модуля; неполный JSON становится честным error/deferred result. Generic GGUF pull уже доступен в `tools/pull_ai_models.py`; веса/llama_cpp не установлены, поэтому `--ai-status` честно показывает роли BLOCKED. | `modules/artist_dossier/manager.py`, `tests/test_ai_layer.py` |

Проверка: `pytest tests/` = **58/58 PASS**; `compileall` OK; data audit = **73/73 managed, 0 unknown, 0 invalid**; AST dead-imports = **0**; `smoke_v26` = **6/6 PASS**; `smoke_v29` = **8/8 PASS**; fallback audit = **0 red flags**; `main.py --ai-status` OK. Версия: **39.8.0**.

---

## КОММИТ v39.7 — PLAN_v39 ШАГ 012 + изоляция checkpoint-ов God Mode (исполнен)

| Блок | Что сделано | Файлы |
|---|---|---|
| 012 | Добавлен `--legacy-off`: runtime не импортирует и не регистрирует патчи `orchestrator_v8..v12`, но legacy-код остаётся для существующих Wizard-сценариев. Loader возвращает прозрачные `enabled/loaded/skipped`. | `main.py` |
| LEGACY-маркировка | Единственный вызов versioned `anti_neuro_v10` в core-пути явно возвращает `stage_marker=LEGACY` и `legacy_stage=anti_neuro_v10`; fallback сохраняет `legacy_attempt`. | `app/core/orchestrator.py` |
| Checkpoint P0 | Обнаружено: `smoke_v29` удалял `out_root`, но God Mode читал старые global checkpoints `output/<project_id>/checkpoints`, из-за чего falsely completed run не создавал `master_god.wav`. `ZSPipeline` получил `checkpoint_dir`; God Mode связывает его с собственным `out_root` и отключает reuse для изолированных запусков. | `app/core/pipeline_core.py`, `app/core/orchestrator_god.py` |
| Регрессии | Добавлены тесты отключения legacy import/registration, CLI wiring, LEGACY marker и custom checkpoint directory. | `tests/test_ai_layer.py` |
| Метаданные | Версия и проектные журналы приведены к v39.7. | `version.json`, `PROJECT_STATE.md`, `SESSION_LOG.md` |

Проверка: `pytest tests/` = **53/53 PASS**; `compileall` OK; `python tools/ast_dead_imports.py` = **0**; `python tools/smoke_v26.py` = **6/6 PASS**; `python tools/smoke_v29.py` = **8/8 PASS**; `python main.py --legacy-off --smoke` = **8/8 PASS**; `python tools/fallback_audit.py` = **0 red flags**; `main.py --help` OK. Версия: **39.7.0**.

---

## КОММИТ v39.6 — PLAN_v39 ШАГ 011 + устранение регрессии smoke_v26 (исполнен)

| Блок | Что сделано | Файлы |
|---|---|---|
| 011 | Добавлен статический AST-граф прямых импортов `app.core`, `modules`, `agents`; lazy-imports внутри функций исключены. Циклы нормализуются и показываются полным путём; allowlist есть, но пуст до появления обоснованного исключения. | `tests/test_ai_layer.py` |
| Регрессия графа | Добавлен искусственный цикл `agents.gamma → app.core.alpha → modules.beta → agents.gamma`, подтверждающий, что детектор действительно падает при петле. | `tests/test_ai_layer.py` |
| Переносимость | Тест роли `essentia` больше не требует локально установленной необязательной `librosa`: проверяется контракт `is_available()` с изолированной подменой модуля. | `tests/test_ai_layer.py` |
| Audio P0 | В `smoke_v26` обнаружена реальная регрессия `beat_stereo`: correlation 0.984–0.986 при пороге ≤0.980. Односторонний Haas-mix заменён контролируемым mid/side widening; исключение больше не подавляется молча. | `modules/beat_constructor.py` |
| Audio-регрессия | Добавлен детерминированный тест конструктора бита с проверкой стереоформата и correlation в диапазоне `[0.3, 0.98]`. | `tests/test_audio_quality.py` |
| Метаданные | Версия, канонический статус и история сессий синхронизированы с фактом проверок. | `version.json`, `PROJECT_STATE.md`, `SESSION_LOG.md` |

Проверка: `pytest tests/` = **49/49 PASS**; `compileall` OK; `python tools/ast_dead_imports.py` = **0**; `python tools/smoke_v26.py` = **6/6 PASS** (beat corr=0.842); `python tools/smoke_v29.py` = **8/8 PASS**; `python tools/fallback_audit.py` = **0 red flags**; `main.py --help/--version` OK. AST-граф: **104 модулей, 18 рёбер, 0 циклов**. Версия: **39.6.0**.

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

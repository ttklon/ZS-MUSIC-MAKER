
---

## КОММИТ — PLAN_v39 ШАГ 038: cover-art quality и fallback (выполнен, runtime BLOCKED)

Добавлен `validate_cover_artifact()`: любой PNG (SDXL или явно маркированный PIL fallback) должен декодироваться, иметь RGB/RGBA и разрешение не менее 512×512 перед попаданием в output проекта. Непригодные файлы возвращают `ok=False` с объективной причиной.

Проверка: 512px RGB PNG проходит; 128px и grayscale PNG отклоняются. `pytest tests/` = **88/88 PASS**; compileall OK; AST dead-imports = **0**. SDXL runtime/weights отсутствуют. Детали: `docs/STEP_STATUS/038_sdxl_cover_quality.md`.

---

## КОММИТ — PLAN_v39 ШАГ 037: SDXL cover_art integration (выполнен, runtime BLOCKED)

`stage_cover` теперь передаёт полученный от SequentialAIRunner SDXL handle в `render_cover_ai`; рендер не создаёт вложенный registry lifecycle. `render_cover_with_pipeline()` записывает PNG или возвращает диагностируемый failure. PIL fallback остаётся явно маркированным и работает только без model handle.

Проверка: fake SDXL создал PNG с прямым handle-вызовом; failing pipeline вернул честный error. `pytest tests/` = **87/87 PASS**; compileall OK; AST dead-imports = **0**. `diffusers`/SDXL weights отсутствуют. Детали: `docs/STEP_STATUS/037_sdxl_cover_integration.md`.

---

## КОММИТ — PLAN_v39 ШАГ 036: DSP quality и fallback (выполнен)

Добавлен `validate_dsp_features()`: BPM должен быть в 40–240, key — хроматическим, duration/RMS — валидными. Неритмический или silent reference не превращается в ложную метрику: dossier сохраняет source audio без ненадёжных DSP данных.

Проверка: валидный payload проходит, BPM=0/invalid key/silent RMS отклоняются. `pytest tests/` = **85/85 PASS**; compileall OK; AST dead-imports = **0**. Детали: `docs/STEP_STATUS/036_essentia_dsp_quality.md`.

---

## КОММИТ — PLAN_v39 ШАГ 035: essentia/librosa DSP integration (выполнен)

Dossier DSP-stage подключена к зарегистрированной роли `essentia`; `extract_dsp_features()` возвращает BPM/key/duration/RMS с честным marker `librosa_dsp`. При runtime-deps absence этап не имитирует метаданные и возвращает explicit skipped. Во время приёмки `librosa` отсутствовал, хотя закреплён в requirements, и был восстановлен из него; real WAV extraction после этого прошёл.

Проверка: реальный 4-second WAV вернул duration/key/RMS; `pytest tests/` = **84/84 PASS**; compileall OK; AST dead-imports = **0**. Подробности: `docs/STEP_STATUS/035_essentia_dsp_integration.md`.

---

## КОММИТ — PLAN_v39 ШАГ 034: CLAP tag quality и fallback (выполнен, runtime BLOCKED)

Добавлен `validate_audio_tags()`: tags должны быть непустым уникальным top-6 subset исходного CLAP vocabulary. При duplicate/unknown/empty output теги очищаются и не передаются как достоверные признаки; при отсутствии CLAP остаётся reference audio без фиктивной разметки.

Проверка: валидный subset проходит; дубликаты и неизвестные label отклоняются. `pytest tests/` = **83/83 PASS**; compileall OK; AST dead-imports = **0**. CLAP runtime/weights отсутствуют. Детали: `docs/STEP_STATUS/034_clap_quality.md`.

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


---
## PLAN_v39 — ШАГ 039: mastering_ai / matchering integration

| Область | Результат |
|---|---|
| Adapter-контракт | Добавлен `master_with_matchering(handle, input_wav, out_wav, reference_wav)`: он использует переданный handle, вызывает `process(target, reference, results=[pcm16])` и не признаёт успехом отсутствие физического output-файла. |
| Runner lifecycle | `stage_master` получает handle от `SequentialAIRunner` и передаёт его в `master_ai`; при reference stage становится role-backed `mastering_ai`, а выгрузка роли остаётся ответственностью runner. |
| Отсутствие reference | Роль не загружается без `reference_master_wav`; сохранён `mastering_pro` fallback с явной причиной `no reference`. |
| Ошибка matchering | Сбой inference либо отсутствие output становятся `fallback_reason`, затем применяется существующий DSP fallback. |
| Регрессии | Добавлены fake-handle тесты успешной передачи `target/reference` и отказа при пустом output. |

Проверка: `pytest tests/test_ai_quality.py -q` = **24 PASS**; `pytest tests/ -q` = **90 PASS**; `compileall` OK; `python tools/ast_dead_imports.py` = **0**. `matchering` отсутствует в sandbox: реальный inference честно **BLOCKED**, но контракт adapter/runner и fallback проверены без тяжёлой зависимости.


---
## PLAN_v39 — ШАГ 040: mastering_ai quality gate

| Проверка | Реализация |
|---|---|
| True peak | `master_audio_metrics()` измеряет 4× oversampled оценку `true_peak_dbtp`; master отклоняется выше **−0.5 dBTP**. |
| Loudness safety | RMS должен находиться в диапазоне **−20…−5 dBFS**. |
| Stereo и time integrity | Output обязан быть 2-channel; длительность должна составлять **0.95–1.05×** длительности mix. |
| Pipeline gate | `stage_master` добавляет `quality`, заменяет `ok` результатом проверки и возвращает конкретную `reason`; успешный engine-output более не равен принятому master-артефакту. |
| Регрессии | Реальные WAV-тесты покрывают допустимый master, peak ceiling, mono, duration, RMS и missing output. |

Проверка: `pytest tests/test_ai_quality.py -q` = **30 PASS**; `pytest tests/ -q` = **96 PASS**; `compileall` OK; `python tools/ast_dead_imports.py` = **0**. Inference matchering в sandbox отсутствует и остаётся честно **BLOCKED**; gate протестирован независимо на реальных аудиоданных.


---
## PLAN_v39 — ШАГ 041: SequentialAIRunner timeout и OOM-защита

| Область | Результат |
|---|---|
| Таймауты стадий | `AIStage.timeout_sec`; default **600 s**, `music_generation`/`music_stereo` **1800 s**, явный stage limit приоритетен. |
| Watchdog | На POSIX main-thread применяется `SIGALRM` с `StageTimeoutError`; daemon timer фиксирует истечение лимита на остальных путях. Timeout возвращает `ok=False`, error и не останавливает последующие стадии. |
| OOM ceiling | До stage и после загрузки роли проверяется VRAM; значение выше budget (default 12 GB) отменяет stage **до вызова fn** с reason `oom: …`. |
| Lifecycle и telemetry | `finally` всегда запускает `registry.unload()`/`gc.collect()`; отчёты теперь включают timeout, VRAM до/после каждой стадии, лог выводит matrix времени/VRAM. |
| Безопасность | Небезопасный kill потока не применяется. Если C/CUDA extension не перехватывает сигнал до возврата, watchdog честно отмечает timeout после возврата и lifecycle всё равно освобождается. |

Проверка: `pytest tests/test_ai_layer.py -q` = **29 PASS**; `pytest tests/ -q` = **99 PASS**; `compileall` OK; `python tools/ast_dead_imports.py` = **0**. Добавлены детерминированные fake-VRAM, timeout и continuation регрессии.

Дополнение приёмки: исправлен приоритет `--ai --dry-run` в `main.py`. Комбинация теперь запускает AI sequential pipeline, а не legacy dry-run. Сквозная проверка завершилась за **0.6 s**: все 12 стадий выдали timeout/VRAM telemetry, музыкальные роли получили **1800 s**, тяжёлые зависимости в sandbox остались честно fallback/skipped.


---
## PLAN_v39 — ШАГ 042: pull-скрипт и manifest 13 AI-ролей

| Область | Результат |
|---|---|
| Единое хранилище | `data/ai_models/<role>/`, а LLM registry/loader синхронизированы с тем же per-role путём. |
| Verification | `manifest.json` содержит source, sizes и SHA-256; `--verify` пересчитывает файл и ловит corruption. Для GGUF закреплены опубликованные LFS SHA-256 и byte sizes. |
| Матрица 13 ролей | GGUF (3), HF snapshots (6), Demucs external cache (1), user-supplied RVC (1), pip-only essentia/matchering (2) — ни одна роль не остаётся неописанной. |
| CLI | Добавлены `--role` (совместимый alias `--model`), `--all`, `--list`, `--verify`; unknown role возвращает exit 1. |
| Честная среда | `mastering_ai` pip-only manifest успешно записан и проверен. `lyrics_llm` pull вернул exit 1: `huggingface_hub` отсутствует; 8.99 GB GGUF не скачан и не заявлен готовым. |

Проверка: `pytest tests/test_ai_model_pull.py -q` = **6 PASS**; `compileall` OK; `python tools/ast_dead_imports.py` = **0**. `huggingface_hub` и heavyweight weights в sandbox отсутствуют, поэтому network download/inference ролей остаётся честно **BLOCKED**.

Дополнение приёмки: full pytest обнаружил, что runtime `data/ai_models/mastering_ai/manifest.json` ошибочно считался неизвестным versioned data. `audit_data_inventory` исправлен: `data/ai_models/` исключён как .gitignored runtime weight storage; добавлен регрессионный тест. Итог: **106 PASS**, inventory **73/73 managed**, **0 unknown**, **0 invalid**.


---
## PLAN_v39 — ШАГ 043: artist dossier demucs→ASR→DSP→CLAP→LLM

| Область | Результат |
|---|---|
| Track pipeline | `DossierManager` последовательно запускает Demucs, ASR, DSP, CLAP и analysis_llm через `SequentialAIRunner`; записи сохраняются per-track. |
| Rich schema | Artist output требует `bio/themes/slang/flow/analogs`, track output — `theme/storyline/key_lines/analysis/hook/reusable_elements`; старые style aliases нормализуются для downstream prompts. |
| Честный unavailable | `analysis_llm` больше не вызывается с `None`: track фиксируется `partial`, report содержит явный skipped reason, artist dossier — deferred note. |
| Реальный CLI fix | `LocalFolderCollector` теперь собирает `.txt` lyrics из пользовательской папки и объединяет их с audio. Smoke `--dossier-add` с local text добавил 1 track; build дал честный deferred при отсутствии LLM. |
| Inventory | `data/artist_dossier/` классифицирован как user-generated runtime output и исключён только из versioned fixture audit. |

Проверка: `pytest tests/test_ai_layer.py -q` = **31 PASS**; `pytest tests/ -q` = **108 PASS**; `compileall` OK; AST = **0**; data inventory **73 managed / 0 unknown / 0 invalid**. Heavy Demucs/ASR/CLAP/LLM inference в sandbox остаётся честно **BLOCKED**.


---
## PLAN_v39 — ШАГ 044: AI-first lyrics + dossier

| Область | Результат |
|---|---|
| Основная ветвь | `stage_lyrics` вызывает `lyrics_gen_ai.generate_lyrics_ai` и передаёт runner handle; nested registry load при model-backed stage исключён. |
| Контекст | Adapter строит prompt с dossier/track reference, BPM/жанром/темой и `user_lyrics_lines`; обязательные строки проверяются в output. |
| Release gate | Добавлены 200–800 words, 2+ verse, repeated hook, user-line inclusion и AI filler checks. Длинный structured lyric получает контролируемую lexical-overlap поправку только с сохранённым line repetition limit. |
| Fallback | Punch library усилен до двух 16-line куплетов с единым повторяемым hook и циклическим punch-list; реальная fallback-regression проходит gate. |
| Честная среда | `lyrics_llm`/llama_cpp отсутствуют: inference не заявлен выполненным, но AI adapter с fake handle, routing и no-model fallback проверены. |

Проверка: `pytest tests/test_ai_quality.py -q` = **33 PASS**; `pytest tests/ -q` = **111 PASS**; `--ai --dry-run` OK; `compileall` OK; AST = **0**.


---
## PLAN_v39 — ШАГ 045: beat_gen_ai / stage_music

| Область | Результат |
|---|---|
| Единый adapter | Inline MusicGen перенесён из `stage_music` в `beat_gen_ai.render_beat_ai`; stage передаёт runner handle, вложенной загрузки registry нет. |
| Audio integrity | Chunks ≤30 s, output обязан иметь не меньше requested samples, затем точно обрезается до целевой длительности и ceiling 0.98. |
| Continuation | `generate_continuation` используется при поддержке handle; несовместимость даёт controlled independent-chunk fallback. |
| Fallback/quality | При недоступной роли сохранён CyberSynth, все ветви проходят audio artifact gate. |
| Reference honesty | `reference_wav` сохраняется как provenance, `reference_applied=False`: не заявляется несуществующее MusicGen audio conditioning. |

Проверка: fake MusicGen/short-output регрессии; `pytest tests/test_ai_quality.py -q` = **35 PASS**, полный `pytest tests/` = **113 PASS**, dry-run/compileall OK, AST = **0**. MusicGen/audiocraft/torch inference в sandbox честно **BLOCKED**.


---
## PLAN_v39 — ШАГ 046: XTTS-v2 → RVC

| Область | Результат |
|---|---|
| Исправление API | `voice_synth_ai` больше не вызывает несуществующий `convert`; использует фактический `rvc_manager.infer(input_wav, voice_name, pitch_shift, out_name)`. |
| Handle lifecycle | XTTS adapter принимает runner `tts_handle`; stage_vocal переведена на этот adapter. RVC может принять `rvc_handle`, standalone path выгружается через registry. |
| RVC honesty | `rvc_applied=True` только после output+quality success; `rvc_model` path не выдаётся за применённую модель без реального `rvc_voice_name`. |
| Quality | К audio metrics добавлен DC offset; RVC отклоняется выше **0.02** вместе с duration/signal constraints. |
| Регрессии | Fake XTTS→RVC проверяет voice name/pitch/project output, отдельный WAV проверяет DC-offset reject. |

Проверка: `pytest tests/test_ai_quality.py -q` = **37 PASS**; полный `pytest tests/` = **115 PASS**; dry-run/compileall OK; AST = **0**. XTTS/rvc-python/user model/GPU в sandbox отсутствуют: real inference честно **BLOCKED**.


---
## PLAN_v39 — ШАГ 047: SDXL cover + font fallback

| Область | Результат |
|---|---|
| Единый размер | `render_cover_ai` передаёт requested `size` и в SDXL, и в PIL fallback; stage contract — **1024×1024**. |
| Production gate | stage_cover требует RGB/RGBA, ≥1024 px и **≥100,000 bytes**. |
| Реальный fallback fix | Измерен flat gradient fallback: 20,108 bytes (недостаточно). Добавлен deterministic film grain для artwork texture, не file padding. |
| Фактический smoke | PIL fallback из AI dry-run: **1024×1024 RGB, 675,292 bytes**; production regression проходит. |
| Переносимость | Font resolver остаётся cross-platform через `font_utils`, без `C:\` path. |

Проверка: `pytest tests/test_ai_quality.py -q` = **38 PASS**; полный `pytest tests/` = **116 PASS**; dry-run/compileall OK; AST = **0**. SDXL/diffusers weights в sandbox отсутствуют, real inference честно **BLOCKED**.


---
## PLAN_v39 — ШАГ 048: matchering + loudness normalization

| Область | Результат |
|---|---|
| Post-matchering | После handle matchering запускается отдельный neutral loudness normalizer; output-file наличие больше не считается достаточной приёмкой. |
| Целевые уровни | Pipeline target установлен на **−14 LUFS**, final sample ceiling **−1.2 dB**, stage quality gate проверяет estimated TP **≤−1.0 dBTP**. |
| Fallback parity | `mastering_pro` fallback проходит тот же final normalizer и возвращает `loudness` evidence. |
| Измерения | `pyloudnorm` путь маркируется `integrated_lufs`; без него строго указывается `rms_approximation`, без фиктивного LUFS claim. |

Проверка: matchering fake WAV contract + `pytest tests/test_ai_quality.py tests/test_mastering_results.py` = **39 PASS**; полный `pytest tests/` = **116 PASS**, compileall/AST OK. matchering/pyloudnorm в sandbox отсутствуют, real integrated-LUFS inference честно **BLOCKED**.


---
## PLAN_v39 — ШАГ 049: замыкание dossier pipeline

`DossierManager` теперь persist-ит успешные промежуточные outputs, ранее жившие только в runner sink: `features.stems.vocals`, `stem_source_index` и `transcript_path`. Уже сохраняемые DSP BPM/key/duration/RMS и CLAP tags остаются в том же track JSON. При недоступных ролях contract по-прежнему честно фиксирует skipped reason без ложного analysis success.

Проверка: `pytest tests/ -q` = **116 PASS**; `compileall` OK; AST = **0**. Demucs/faster-whisper/CLAP weights в sandbox отсутствуют: real inference **BLOCKED**.


---
## PLAN_v39 — ШАГ 050: stereo textures в mix

`stage_mix` теперь использует `music_stereo.texture_path`: texture ресемплируется/upmix-ится при необходимости и подмешивается к beat с RMS-relative gain **−18 dB**, затем проходит peak ceiling. Result содержит `texture_mixed=True/False`, поэтому отсутствие MusicGen texture остаётся честно наблюдаемым и не ломает base mix.

Проверка: `pytest tests/ -q` = **116 PASS**; `compileall` OK; AST = **0**. MusicGen stereo weights отсутствуют в sandbox, реальная генерация texture **BLOCKED**.


---
## PLAN_v39 — ШАГ 051: GUI статус AI

В Wizard добавлена страница AI status и меню `AI → Статус моделей`: она показывает все 13 roles, public availability, engine, VRAM estimate и текущую sequential role без загрузки весов. Обновление доступно вручную и раз в 5 секунд.

Проверка: `compileall app/gui/wizard.py app/ai/registry.py` OK; `pytest tests/` = **116 PASS**; AST = **0**. В headless sandbox PySide interaction не запускалась; UI использует проверенный `ModelRegistry.status()`/`is_available()` API.


---
## PLAN_v39 — ШАГ 052: render queue

`RenderQueue` дополнена явным `cancelled` state и `cancel_requested` для running jobs. Pending отменяется немедленно, running job завершается отменой на следующей stage callback boundary; это не пытается небезопасно убить нативную AI-стадию посередине. FIFO worker, progress persistence и restart restore сохранены.

Проверка: новые fake-orchestrator FIFO/cancel/persistence тесты = **2 PASS**; полный `pytest tests/` = **118 PASS**; compileall/AST OK.


---
## PLAN_v39 — ШАГ 053: session manifest schema

AI pipeline теперь создаёт `manifest.json` с `schema_version=1`, wizard state, stage report, engine/file/HF provenance 13 ролей и artifact map. `project_meta.json` сохранён для обратной совместимости. Regression проверяет manifest в isolated dry project output.

Проверка: `pytest tests/test_ai_layer.py` = **32 PASS**; полный `pytest tests/` = **119 PASS**; compileall/AST OK.


---
## PLAN_v39 — ШАГ 054: genre preset validation

`genre_validator` разделён на проверку **50/50 versioned JSON assets** по фактической schema и проверку **119 runtime genres** через `GenreFactory`. Реальный запуск: `Preset assets: 50/50`, `Runtime genres: 119`, `PASS`.

Проверка: validator OK; полный `pytest tests/` = **119 PASS**; compileall/AST OK.


---
## PLAN_v39 — ШАГ 055: Phonk engine unification

Исправлен фактический API-разрыв: V2 вызывал cowbell как in-memory frequency/duration primitive, legacy V1 принимал только file-output аргументы. `phonk_engine` теперь canonical primitive с modern ndarray и backward-compatible WAV adapter; V2 остаётся advanced composition layer.

Проверка: phonk waveform + legacy output tests = **2 PASS**; полный `pytest tests/` = **121 PASS**; compileall/AST OK.


---
## PLAN_v39 — ШАГ 056: Voice Vault → XTTS speaker_wav

Добавлен `select_speaker_wav`: выбор clean recording по стилю/SNR с исключением clipped clips и controlled fallback. `stage_vocal` использует explicit `speaker_wav` или выбранный Voice Vault clip. В проверке выявлен и исправлен first-import bug: vault directory создаётся до `copy2`, не только перед index save.

Проверка: Voice Vault WAV intake/selection tests = **2 PASS**; полный `pytest tests/` = **123 PASS**; compileall/AST OK.


---
## PLAN_v39 — ШАГ 057: authorized remix workflow

Добавлен `modules.remix.render_remix`: remix возможен только с явным `source_authorized=True`, использует новый beat и vocal stem без source looping, ресемплирует к beat sample rate, гарантирует stereo и peak ceiling. Demucs dossier stem остаётся аналитическим; его применение требует прав пользователя.

Проверка: remix authorization/audio tests = **2 PASS**; полный `pytest tests/` = **125 PASS**; compileall/AST OK.


---
## PLAN_v39 — ШАГ 058: release export + fingerprints

`release_export` теперь добавляет SHA-256 всех существующих package artifacts в `manifest.json` и формирует `release.zip`. Metadata/ISRC и optional ID3/MP3/FLAC путь сохранены; WAV/metadata/manifest/archive остаются обязательным baseline без зависимости от ffmpeg.

Проверка: release WAV package regression = **1 PASS**; полный `pytest tests/` = **126 PASS**; compileall/AST OK.


---
## PLAN_v39 — ШАГ 059: RVC trainer honesty

Исправлен training job persistence (`JOBS_DIR` создаётся до записи). Dry training фиксирует `done_dry` и явное отсутствие `.pth`; trainer API без верифицированного checkpoint даёт `done_unverified`, не ложный `done`.

Проверка: RVC dry job regression = **1 PASS**; полный `pytest tests/` = **127 PASS**; compileall/AST OK. Real RVC training/export .pth требует runtime/GPU и честно **BLOCKED** в sandbox.


---
## PLAN_v39 — ШАГ 060: hit scoring CLI

Существующий audio-first `hit_scorer.score_track` подключён к `main.py --score <master.wav>`: CLI выводит hit score, verdict, 12 metric breakdown, actions и TikTok slice. Это техническая эвристика структуры/энергии, не обещание коммерческого успеха и не LLM-оценка лирики.

Проверка: score CLI regression = **33 PASS** в `test_ai_layer`; полный `pytest tests/` = **128 PASS**; compileall/AST OK.


---
## PLAN_v39 — ШАГ 061: AI detector risk contract

`ai_detector_pro` теперь отдаёт `ai_risk_percent` 0–100 и `metric_type=internal_audio_heuristic_not_ai_attribution`. Это делает internal quality signal для динамики/периодичности/спектра явным, не выдавая его за доказательство происхождения аудио или объективную «человечность».

Проверка: synthetic detector regression = **1 PASS**; полный `pytest tests/` = **129 PASS**; compileall/AST OK.


---
## PLAN_v39 — ШАГ 062: installer hardening

`install.py` теперь использует only argv subprocess calls без shell; core manifest по умолчанию, `requirements_ai.txt` только через `--ai`, Linux packages только через `--system-deps`. `--dry-run` создаёт required runtime dirs, печатает план и не устанавливает пакеты.

Проверка: installer unit tests = **2 PASS**; полный `pytest tests/` = **131 PASS**; compileall/AST OK. Реальный pip/GPU install в sandbox намеренно не запускался.


---
## PLAN_v39 — ШАГ 063: safe updater status

Добавлен `main.py --update` → `check_git_update_status`: report включает branch, local/remote revision, relation, чистоту дерева и `apply_performed=false`. Проверка читает Git status/remote revision и не выполняет fetch/pull/reset/checkout/install/rollback.

Проверка: `main.py --update` OK; updater read-only regression = **1 PASS**; полный `pytest tests/` = **132 PASS**; compileall/AST OK.


---
## PLAN_v39 — ШАГ 064: security path и redaction

Добавлены `safe_identifier`/`safe_child_path` против path traversal и `redact_secrets` для GitHub/API/Bearer-shaped tokens. Central logger применяет redacting filter к file/console handlers. Scoped audit Python-кода не обнаружил PAT-shaped значения.

Проверка: security tests = **2 PASS**; полный `pytest tests/` = **134 PASS**; compileall/AST OK; PAT pattern grep = **0**.


---
## PLAN_v39 — ШАГ 065: performance cache

Добавлен bounded mtime-keyed LRU decode/resample cache для повторного `hit_scorer.score_track` одного неизменённого WAV. Изменение source mtime инвалидирует key. Это точечная оптимизация non-AI hot path без обещания ускорения full pipeline/inference.

Проверка: cache regression = **1 PASS**; полный `pytest tests/` = **135 PASS**; compileall/AST OK.


---
## PLAN_v39 — ШАГ 066: test suite expansion

Test suite при приёмке: **137 collected / 137 PASS**, существенно выше планового ≥60. Добавлены direct regressions 50 versioned genre preset schema и 119 runtime factory profiles; ранее добавленные tests покрывают AI adapters, quality, runner, dossier, vault, release, installer, updater, security и RVC dry contract.

Проверка: targeted genre tests = **2 PASS**; полный `pytest tests/` = **137 PASS**; compileall/AST OK. Line coverage percentage честно не заявлен без зафиксированного coverage tool.


---
## PLAN_v39 — ШАГ 067: CI/CD release workflow

`build.yml` теперь запускается также на тегах `v*`; после успешной Windows PyInstaller build `publish-release` архивирует artifact и создаёт GitHub Release. На main без тега релиз не создаётся, artifact сохраняется 30 дней. Windows runner/tag release локально не запускались.

Проверка: полный `pytest tests/` = **137 PASS**; compileall/AST OK; workflow diff без whitespace errors.

---
## PLAN_v39 — ШАГ 068: документация v39

README, INSTALL и CHANGELOG обновлены до v39.9.0; добавлен `docs/DEVELOPER_GUIDE.md`. Документированы только работающие CLI contracts: AI status/dry-run, dossier, score, read-only updater и opt-in installer/model-pull. Heavy dependencies/weights явно остаются environment-dependent BLOCKED при отсутствии runtime.

Приёмка: `main.py --help`, `--ai-status`, `pull_ai_models.py --help` успешны; README relative links 2/2 существуют; `pytest tests/ -q` = **137 PASS**, compileall/AST OK.

---
## PLAN_v39 — ШАГ 069: PROJECT_STATE и readiness

`tools/readiness.py` теперь строит воспроизводимую AST/static-reference inventory только по versioned production `.py`, сохраняет прежний `compute()` JSON-контракт и поддерживает `--inventory-markdown`. Удалены пустые dependency `try` probes и legacy v14 test markers; optional heavy engines в sandbox честно BLOCKED.

PROJECT_STATE заменён v39 snapshot: **147/147** matrix rows соответствуют tracked production modules (140 REAL_PASS static, 0 REAL_FAIL, 7 PLANNED). Это не объявляет heavy runtime/inference выполненным. Приёмка: readiness JSON/matrix match, `pytest tests/ -q` = **141 PASS**, compileall/AST OK.

---
## PLAN_v39 — ШАГ 070: APP_G регресс-сценарии

Добавлен воспроизводимый `tools/regress_v39.py` и 15-сценарная matrix `docs/REGRESS_v39.md`. Фактический прогон: **13 PASS, 2 BLOCKED, 0 FAIL**. BLOCKED: полный heavy 13-role runtime и 300-second MusicGen — sandbox не содержит нужных dependencies/weights/GPU; они не выданы за реальный inference. Машинное evidence: `docs/REGRESS_v39.results.json`.

Приёмка: runner self-tests 3 PASS; полный `pytest tests/ -q` = **144 PASS**, compileall/AST OK.

---
## PLAN_v39 — ШАГ 071: golden-тесты звука

Добавлены versioned fixtures `tests/fixtures/audio/golden_beat_15s.wav` и `golden_master_10s.wav`, generator и metric helper. Golden tests сравнивают 15s fixed-seed beat и 10s local DSP master по duration, RMS, peak, spectrum/correlation с допусками, а не по хрупкому byte equality. `.gitignore` разрешает только `tests/fixtures/audio/golden_*.wav`.

Приёмка: focused golden tests = **8 PASS**; полный suite до финального fixture tracking check = **148 PASS**, AST=0. Matchering runtime не установлен: master fixture покрывает ProAudioDSP, не заявляется Matchering inference.

---
## PLAN_v39 — ШАГ 075: единый CLI-стиль tools

Выполнен audit 19 executable tools. `--help` раньше у части scripts запускал smoke/E2E/deep audit или падал на optional deps. Добавлен safe shared help guard для no-option tools, `readiness` переведён на собственный argparse parser, `p0_truth_test` получил main/exit contract, `ab_compare` lazy-check optional pyloudnorm, `validate_final_track` argparse. Все **19/19** `python tools/<script> --help` теперь дают usage и rc=0 без workload; contract покрыт тестом.

Первичный небезопасный audit создал deep-audit reports и ignored health JSON; они полностью удалены/восстановлены, data inventory вновь **73 managed, 0 unknown, 0 invalid**. Финальная приёмка: `pytest tests/ -q` = **167 PASS**, compileall/AST OK.

---
## PLAN_v39 — ШАГ 076: prompt catalog и привязка к ролям

Все 15 versioned `.prompt.txt` ранее не читались runtime. В `app/ai/prompts.py` добавлен allowlisted role catalog: lyrics=4, metadata=8, analysis=1, cover_art=1, trend_analysis=1. Loader отклоняет произвольные filenames, renderer валидирует placeholders; builders lyrics/dossier/metadata используют role assets, cover asset проверяется без изменения совместимого concise prompt.

Приёмка: 15/15 mapped/renderable, catalog tests 4 PASS, unknown/path traversal name rejected. `pytest tests/ -q` = **171 PASS**, compileall/AST OK, data inventory 73/0/0. Heavy inference не заявляется.

---
## PLAN_v39 — ШАГ 077: lyrics_gen_v8 deprecation и AI-first legacy path

`lyrics_gen_v8` сохранён для Wizard compatibility, но импорт явно выдаёт DeprecationWarning. `orchestrator_v8_patch` сначала проверяет availability `lyrics_llm`; только при доступной роли вызывает `lyrics_gen_ai` и конвертирует result в legacy recipe fields. При отсутствии/ошибке role честно возвращается к v8 generator, так что warning/fallback не скрывают blocked model.

Приёмка: 4 targeted tests (warning, unavailable role, fake AI output, v8 preference) PASS; полный `pytest tests/ -q` = **175 PASS**, compileall/AST OK, data inventory 73/0/0. Real LLM inference не запускался.

---
## PLAN_v39 — ШАГ 078: общий LLM service resilience

`app.ai.llm_service` теперь даёт default timeout=600, retry=2, daemon-bounded timeout и circuit breaker после трёх failed requests, сохраняя string API и callable llama fallback. `llm_clients_v15.complete_local_handle()` делегирует shared service и возвращает structured router-style failure/success без fake template content.

Приёмка: fake-handle tests покрыли 3rd-attempt recovery, timeout, circuit, chat→callable compatibility и идентичный v15/shared text. Полный `pytest tests/ -q` = **180 PASS**, compileall/AST OK, data inventory 73/0/0. Real model/network inference не запускался.

---
## PLAN_v39 — ШАГ 079: artist dossier schema и migration

Добавлен versioned `data/artist_dossier/schema.json` v1; tracked только schema, runtime dossier JSON остаются ignored. Manager нормализует aliases/schema_version, валидирует complete dossiers при aggregate/save, отклоняет новые incomplete payloads, а неполный legacy artist JSON при чтении честно мигрирует в deferred с причиной.

Приёмка: 4 schema/migration tests PASS; полный `pytest tests/ -q` = **184 PASS**, compileall/AST OK, data inventory 73/0/0. Реальный analysis LLM не запускался.

---
## PLAN_v39 — ШАГ 080: metadata release quality

Metadata validator теперь требует title 3–80, обе descriptions 20–400, максимум 8 unique normalized tags и отсутствие AI filler. `stage_metadata` использует genre-aware deterministic fallback, который проходит тот же gate; LLM invalid/missing output не сохраняется как valid metadata.

Приёмка: boundary/dry-run tests PASS; полный `pytest tests/ -q` = **185 PASS**, compileall/AST OK, data inventory 73/0/0. Heavy metadata LLM inference не запускался.

---
## PLAN_v39 — ШАГ 081: MusicGen stereo beat extension

Добавлен deterministic WAV crossfade helper для intro/base/outro. При доступном music_stereo handle stage генерирует/валидирует обе stereo sections, собирает `beat_stereo_extended.wav`, и mix предпочитает этот beat. Любая unavailable/quality/generation failure возвращает explicit skipped/fallback и сохраняет base beat; dry-run не симулирует MusicGen.

Приёмка на real temporary WAV с разными sample rates подтвердила resampling, 2-channel output, peak <=0.981 и expected crossfade duration. Полный `pytest tests/ -q` = **187 PASS**, compileall/AST OK, data inventory 73/0/0. MusicGen weights BLOCKED.

---
## PLAN_v39 — ШАГ 082: voice cleaner chain

`clean_vocal_chain` реализует denoise -> zero-phase 4.5–9.5 kHz de-esser -> smoothed silence gate с genre presets и measured pause metric. `process_vocal` запускает cleanup до double/throw. На synthetic 32 kHz vocal: pauses < -60 dBFS, sibilance reduction около 3 dB, 12 kHz air не затронут существенно; optional noisereduce отсутствует и fallback явно маркируется.

Приёмка: 2 targeted synthetic tests PASS; полный `pytest tests/ -q` = **189 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 083: five-slot beat constructor

Добавлены genre-aware 16-step slots kick/snare/hat/bass/melody, deterministic 8-bar plan и MIDI exporter contract. Отдельный phonk bass pattern больше не дублирует kick. После обнаруженного golden RMS regression legacy constructor default сохранён отдельным `legacy` preset; новые genre-aware calls получают новые slots, а existing default fixture остаётся воспроизводимой. mido отсутствует — five-slot MIDI export честно BLOCKED, events доступны.

Приёмка: 8 bars/stereo <5s, five slots по 128 steps, golden rerender зелёный. Полный `pytest tests/ -q` = **193 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 084: render queue priority and persistence

RenderQueue now persists to `queue.json`, reads the legacy state file only for compatibility, supports numeric priority with FIFO ties, and persists `set_priority`. Pending cancellation remains terminal; restart returns only non-cancelled running work to pending and retains cancellation requests as cancelled.

Приёмка: scenario of 3 tasks/cancelled middle/high-priority third/restart recovery PASS. Полный `pytest tests/ -q` = **194 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 085: user creative preferences

User profile now stores validated non-PII genres/language/text style/default beat; a narrow prompt projection excludes artist name and history. Lyrics, metadata and music prompt builders honor this projection. An initial full suite exposed an unwanted default-prompt write of `data/user_profile.json`; corrected prompt defaults are now read-only and the artifact was removed.

Приёмка: preference persistence/PII exclusion regressions PASS; полный `pytest tests/ -q` = **197 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 086: RU/EN i18n

Создан runtime i18n с RU/EN dictionaries, `t()` и переключением языка без рестарта. `ZSMM_LANGUAGE` читается из config; wizard nav/menu и pipeline lifecycle используют translated labels, сохраняя stable machine statuses.

Приёмка: i18n/config/pipeline regressions PASS; полный `pytest tests/ -q` = **201 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 087: auto backup preflight

Создан bounded `data/backups/<timestamp>` snapshot before explicit `--ai`/`--god` paths, с SHA-256 manifest, restore verification и retention 7 дней. Backup excludes runtime models/backups and copied source data is capped at 50 MB; failure is visible warning, not false success or silent render block.

Приёмка: temporary snapshot/restore/checksum/size/retention and preflight reporting PASS; полный `pytest tests/ -q` = **204 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 088: dependency licenses

`readiness.py --licenses` now generates versioned `docs/LICENSES.md` from base and optional-AI manifests using `importlib.metadata`. The report inventories 46 direct dependencies, labels unavailable metadata UNKNOWN rather than guessing a license, and carries a GPL compatibility review checklist for unknown/transitive/model/content scope.

Приёмка: license parser/metadata/report tests and real CLI PASS; полный `pytest tests/ -q` = **207 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 089: execution manifest report

`readiness.py --report` generates versioned `PLAN_v39_EXEC_REPORT.md` from 100 plan headings and actual git subjects only, including explicit `ШАГИ NNN–MMM` ranges. It never converts files/tests/session claims into committed evidence; unmatched headings remain PENDING. Pre-commit report evidence was 85/100, correctly excluding the then-uncommitted ШАГ 089 itself.

Приёмка: plan/range/committed-vs-pending/CLI regressions PASS; полный `pytest tests/ -q` = **211 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 090: DSP spectral goldens

Versioned deterministic local-DSP fixtures now cover beat 15s, vocal 10s and master 10s. Vocal baseline is generated from inspectable synthesis, and duration/RMS/peak/centroid regression checks enforce <=5% drift where applicable. Matchering optional runtime remains BLOCKED and is not presented as golden inference.

Приёмка: targeted goldens 14 PASS; полный `pytest tests/ -q` = **213 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 091: classical seed determinism

BeatConstructor now uses isolated Python/NumPy RNGs when a seed is supplied; same seed produces byte-identical classic WAVs while a different seed differs. CyberSynth exposes only `classical_local_dsp_only` determinism metadata; AI stages are not claimed deterministic. Legacy unseeded golden behavior remains preserved.

Приёмка: same-seed beat/CyberSynth bytes equal, changed beat seed differs, golden stays green; полный `pytest tests/ -q` = **215 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 092: dependency profiles

pyproject now mirrors base/AI/AMD requirement profiles through extras; torch-heavy packages remain outside default install. Contract tests verify package-name parity for all three manifests and explicitly ensure the heavy AI stack is optional.

Приёмка: dependency profile tests PASS; полный `pytest tests/ -q` = **217 PASS**, compileall/AST OK, data inventory 73/0/0. Heavy packages не устанавливались.

---
## PLAN_v39 — ШАГ 093: genre cover prompts

All 50 versioned genre presets now carry renderable `prompt_cover` and `cover_instruments` metadata. Validator enforces mood/key/instruments placeholders; cover_art_ai renders preset direction and stage_cover passes the actual key. SDXL remains optional/BLOCKED, while the prompt contract is fully tested.

Приёмка: validator 50/50 assets and 119 runtime genres PASS; полный `pytest tests/ -q` = **220 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 094: KPI telemetry без PII

KPI history now stores only a schema-v1 allowlist: stage duration, VRAM, score, status, aggregate pipeline metrics and verdict. Project IDs, lyrics/notes, prompt text, release paths and filenames are excluded; unsafe stage labels are redacted. KPI dashboard consumes only valid sanitized telemetry lines.

Приёмка: raw JSONL privacy assertions and dashboard metric rendering PASS; полный `pytest tests/ -q` = **222 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 095: офлайн-режим с явным разрешением сети

Freesound search/download и GitHub/release update checks теперь deny-by-default: удалённые вызовы запускаются только через `--online`/`allow_online=True` либо пользовательское `network.online=true`. `--ai --dry-run` выполнен офлайн; model deps/weights отсутствуют и честно прошли fallback, без заявлений об inference. Созданный runtime backup удалён после проверки.

Приёмка: mocked network regression PASS; `pytest tests/ -q` = **226 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 096: legacy-off compatibility report

Core now declares a factual v8–v12 compatibility manifest. `--legacy-off` prints the disabled entrypoints before dispatch (including `--smoke`) without importing patch modules; `--legacy-report` displays the same matrix independently. The report distinguishes omitted legacy compatibility behavior from the modern core's CPU path.

Приёмка: `python3 main.py --legacy-off --smoke` printed five disabled entries and produced **8 PASS / 0 FAIL**; mido/torch/TTS absences stayed honest BLOCKED/fallback. `pytest tests/ -q` = **229 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 097: wheel + clean venv

Published packaging metadata now installs `main.py` and exposes `zs-music-maker`. Dynamic package metadata uses a static `VERSION` mirror guarded against `version.json` drift; source checkout version lookup remains canonical and installed wheels use distribution metadata.

Приёмка: `python3 -m build` создал wheel; чистый `/tmp` venv установил wheel с `--no-deps`, а `zs-music-maker --version` и установленный `python -m main --version` вне checkout вернули 39.9.0. `pytest tests/ -q` = **230 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 098: terminal AI stage progress

Добавлен dependency-free console renderer real stage lifecycle: START/finish для 12 AI-стадий с measured duration, VRAM and explicit OK/FALLBACK/SKIPPED/FAILED status. CLI `--ai` и `--ai --dry-run` включают его явно; API default remains quiet. Callback errors do not interrupt rendering.

Приёмка: live `--ai --dry-run` дал 12 START и 12 finish records; final `12/12 FALLBACK tag` честно отражает отсутствующий optional model/runtime. Runtime backup удалён. `pytest tests/ -q` = **232 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 099: CPU classical pipeline baseline

`run_full_pipeline()` теперь возвращает public `master_path` for its streaming master. Added no-torch regression executes a non-dry local-DSP pipeline (instrumental mode), decodes the actual output WAV and verifies duration, sample rate, channels, finite data and non-silence. This is a CPU classical baseline, not a claim of absent heavy AI/TTS/RVC inference.

Приёмка: `tests/test_classical_determinism.py` = **3 PASS**, including real CPU master; полный `pytest tests/ -q` = **233 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 072: release preflight и честная стратегия тега

Добавлен read-only `tools/release_preflight.py`: branch/main, clean tree, `version.json`↔`VERSION`, packaging console entrypoint и локальная/remote availability source-implied tag. Canonical version уже 39.9.0, поэтому финальный кандидат — `v39.9.0`; противоречивый старый target `v39.0.0` не применяется как downgrade. Clean-head preflight/tag проверяется на финальном шаге.

Приёмка: targeted 2 PASS; `pytest tests/ -q` = **235 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 073: execution report из git evidence

`tools/readiness.py --report` regenerated `docs/PLAN_v39_EXEC_REPORT.md` directly from commit subjects. Snapshot at clean post-072 head: **100 headings, 97 COMMITTED, 3 PENDING** — only current 073, 074 and final 100. It does not count uncommitted work or assert code-quality from a commit subject. Final release will regenerate it after the remaining three commits.

---
## PLAN_v39 — ШАГ 074: plan integrity и память

Добавлен read-only `tools/plan_integrity.py`: strict UTF-8, final newline, same primary heading grammar as execution report, exact ordered 001–100, byte/char/line metrics and SHA-256. Measured PLAN_v39: 3,595,003 bytes; 2,419,839 chars; 26,254 lines; SHA-256 `84c048cd1b223cd375ad2bcac01e8cef9d92bb09f934414d18d28c9e31775e87`.

Приёмка: integrity tests 2 PASS; `pytest tests/ -q` = **237 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## PLAN_v39 — ШАГ 100: финализация v39.9.0

Canonical version stays **39.9.0** (not the stale conflicting v39.0.0 target): version metadata and CHANGELOG now identify the completed PLAN_v39 release. Final APP_G: **13 PASS, 2 BLOCKED, 0 FAIL**; BLOCKED is the documented absent heavy runtime/model path, not fake inference. Generated APP_G runtime backups were removed before inventory acceptance.

Локальная приёмка: `pytest tests/ -q` = **237 PASS**, compileall OK, AST 0 dead imports, data inventory 73/0/0, strict plan integrity 001–100, `main.py --version` = 39.9.0 finalisation build. After this commit, execution report is regenerated from commit evidence to 100/100, then clean-head preflight and annotated v39.9.0 tag push provide final release evidence.

### Final execution-evidence refresh

После commit `6d8b3a75` повторный `tools/readiness.py --report` подтвердил **100/100 COMMITTED, 0 PENDING**. Таблица связывает ШАГ 073 с `1fb08065`, ШАГ 074 с `c42e4c2d` и ШАГ 100 с `6d8b3a75`; статус выводится только из git subject evidence.

### Tag and GitHub release verification

Annotated `v39.9.0` and public release <https://github.com/ttklon/ZS-MUSIC-MAKER/releases/tag/v39.9.0> were verified at `864c486aa5d7a16f5f5cbb2f8acbf0fc42064dae` / origin/main. The tag workflow run `32561256890` failed before `build-windows` got a runner or executed a step; publish-release was skipped and release assets are empty. The source release was published manually with this disclosed; no CI-built Windows EXE is claimed.

---
## APP_L v40 — triage ШАГОВ 0001–0004: SECURITY_EVAL

Проверены все 4 CRITICAL findings: `QDialog.exec()`/`QApplication.exec()` — Qt event loops, не Python builtin dynamic execution. Исправлен source false positive in `deep_audit_v40`: SECURITY_EVAL теперь только direct AST Name calls `eval`/`exec`; regression keeps real builtins flagged and Qt attribute calls excluded.

Приёмка: focused 2 PASS; `pytest tests/ -q` = **239 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## APP_L v40 — ШАГИ 0005–0008: portable paths

Исправлены confirmed POSIX literals in release-pack CLI example, video self-test and settings fixture through `tempfile`/pytest `tmp_path`. Audit item 0007 was stale: current cited AI-layer source has no `/tmp/unused.txt`, so no unrelated test was changed just to close an outdated line reference.

Приёмка: focused 9 PASS; `pytest tests/ -q` = **242 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## APP_L v40 — triage ШАГОВ 0009–0119: DEAD_IMPORT baseline

Deep audit больше не трактует `from __future__ import annotations` как runtime dead import: это compiler directive. Regression сохраняет detection реального unused import. Remaining reexports/ordinary imports не удаляются механически и требуют semantic review.

Приёмка: focused 3 PASS; `pytest tests/ -q` = **243 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## APP_L v40 — semantic DEAD_IMPORT cleanup

Deep audit aligned with established AST semantics: ignores `__future__` directives, relative reexports and explicit `# noqa`, while still flagging real unused imports. Removed confirmed unused ImageFont, test Path, test os/Path; preserved optional torch_directml probes and package API exports. Regenerated raw audit: **923** findings / 209 files, with no false claim that other categories are closed.

Приёмка: targeted 13 PASS; `pytest tests/ -q` = **244 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## APP_L v40 — SILENT_EXCEPT_PASS: GUI theme diagnostic

`main._try_launch_gui_pyside()` больше не молча подавляет сбой `theme_v12.apply(app)`: Wizard startup retains non-fatal fallback but emits `_safe_print` with exception reason. Focused fake-GUI test verifies diagnostic and normal event-loop exit; other structured fallback handlers remain out of this scoped semantic change.

Приёмка: focused 1 PASS; `pytest tests/ -q` = **245 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## APP_L v40 — path audit scope

HARDCODED_POSIX_PATH now evaluates production sources only; deliberate test PII/path fixtures and the detector’s own regex are no longer HIGH deployment findings. Production scanning remains enabled. Regenerated audit: **917** findings / 210 files, with **1** remaining production POSIX path explicitly not closed here.

Приёмка: focused 5 PASS; `pytest tests/ -q` = **246 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## APP_L v40 — zero production POSIX paths

Последний HARDCODED_POSIX_PATH был self-descriptive pattern in `deep_audit_v40_expand.py`, not runtime filesystem target. Audit meta-tools joined excluded test fixtures only for this source-pattern category; ordinary production/tools scanning stays enabled. Fresh audit: **0** HARDCODED_POSIX_PATH, **916** total findings / 210 files.

Приёмка: focused 6 PASS; `pytest tests/ -q` = **247 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## APP_L v40 — initial remediation matrix

Fresh clean-head audit scanned 210 Python files: **916** heuristic findings. SECURITY_EVAL/OS_SYSTEM/SHELL_TRUE and hardcoded Windows/POSIX path categories are now 0 detector records. This does not claim formal security proof: BARE_PRINT 326, docstrings 381 combined, SILENT_EXCEPT_PASS 121, complexity/long-function/sleep/global/XXX categories remain open for semantic per-item work.

---
## APP_L v40 — GLOBAL_STATEMENT: settings cache

`config.settings` migrated from mutable `_settings`/`global` assignments to bounded `lru_cache(maxsize=1)`; `reset_settings()` now cache_clear() and preserves test contract. New regression verifies stable snapshot before reset and environment reload after reset.

Приёмка: targeted 7 PASS; `pytest tests/ -q` = **248 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## APP_L v40 — actionable marker classification

Deep audit marker detection now matches only leading actionable comment labels (`# TODO:`, `# FIXME -`, etc.). ISRC schema prose `XX-XXX-00-00000` is no longer false MARKER_XXX; explicit TODO remains detected. Fresh audit: 0 marker findings, 2 GLOBAL_STATEMENT, 913 total heuristic findings / 210 files.

Приёмка: focused 7 PASS; `pytest tests/ -q` = **249 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## APP_L v40 — interruptible worker waits

Runtime and render idle loops now use stop-aware `Event.wait(timeout)` rather than uninterruptible sleeps. `RuntimeOrchestrator.stop(join_timeout)` added for bounded public shutdown. Idle-worker regression starts both workers and proves clean stop/join in <0.5s without starting an audio pipeline.

Приёмка: targeted 4 PASS; `pytest tests/ -q` = **250 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## APP_L v40 — mastering capability isolation

`process_mastering()` no longer mutates global optional-DSP import flags after a single runtime failure. Per-run pedalboard/loudnorm flags select the current fallback only; `normalize_master_loudness()` mirrors local capability scope. Regression injects failing AudioFile, validates numpy fallback output and proves HAS_PEDALBOARD stays true.

Приёмка: focused 1 PASS; `pytest tests/ -q` = **251 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## APP_L v40 — i18n state encapsulation

Process-local i18n `_current_language` scalar replaced with private `_LanguageState` under the existing RLock. Public set/get/translation behavior preserved; audit now reports **0 GLOBAL_STATEMENT** findings. Targeted i18n tests recovered after fixing one legacy accessor reference.

Приёмка: targeted 4 PASS; `pytest tests/ -q` = **251 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## APP_L v40 — nonblocking Gradio expert launch

Wizard Gradio warm-up no longer blocks Qt UI with `time.sleep(2)`: browser launch is scheduled by daemon-compatible `threading.Timer`. Full acceptance initially caught obsolete Wizard `time` import; removed it, then full suite passed. Focused AST test proves Timer/no-sleep contract without GUI/server startup.

Приёмка: focused 1 PASS; `pytest tests/ -q` = **252 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## APP_L v40 — karaoke stop responsiveness

Karaoke count-in and poll waits now use session Event.wait, preserving normal timing while immediate stop exits worker and retains `stopped` rather than overwriting it with `finished`. Regression stops a one-minute count-in after first beat and proves join in <0.5s without audio/microphone.

Приёмка: focused 1 PASS; `pytest tests/ -q` = **253 PASS**, compileall/AST OK, data inventory 73/0/0.

---
## APP_L v40 — voice-recording split decomposition

`split_wav_into_takes` was decomposed from 117 LOC into WAV load, frame-analysis and take-persistence helpers while retaining the 20 ms, threshold, take and manifest contracts. Real temporary-WAV regression verifies two voiced regions, persisted take files and matching JSON manifest without microphone access.

Приёмка: focused 1 PASS; `pytest tests/ -q` = **254 PASS**, compileall/AST OK, data inventory 73/0/0. Fresh audit: **29 LONG_FUNCTION** (was 30); `modules/voice_recording.py` no longer has a long-function finding; total 909 heuristic records across 215 files.

---
## APP_L v40 — RVC training honesty

Non-dry RVC requests no longer advance fake epochs after import detection and report `done_unverified`. They terminate as `blocked_backend` with a persisted statement that no backend invocation/model output was claimed. The short dry path remains explicitly labeled CI/UI simulation and continues to report no model.

Приёмка: focused RVC suite 2 PASS; `pytest tests/ -q` = **255 PASS**, compileall/AST OK, data inventory 73/0/0. Fresh audit: RVC has 0 `BLOCKING_SLEEP`; category is **8** (was 10), total **908** heuristic records across 215 files.

---
## APP_L v40 — voice-onboarding manifest observability

Malformed/unreadable persisted onboarding manifests retain the compatible empty-plan fallback but now emit a narrow JSON/I/O warning rather than being silently swallowed. Missing first-run manifest remains quiet. Regression verifies fallback shape and warning in a temporary file.

Приёмка: focused 1 PASS; `pytest tests/ -q` = **256 PASS**, compileall/AST OK, data inventory 73/0/0. Fresh audit: **120 SILENT_EXCEPT_PASS** (was 121), none in `modules/voice_onboarding.py`; total **907** heuristic records across 216 files.

---
## APP_L v40 — RuntimeOrchestrator result decomposition

`RuntimeOrchestrator._process` now keeps lifecycle/error handling only; pure `_summarize_pipeline_result` owns stage traversal and the existing desktop result contract. Regression checks polish/master precedence, release data and sanitized hit/warning fields without starting a full pipeline.

Приёмка: focused 1 PASS; `pytest tests/ -q` = **257 PASS**, compileall/AST OK, data inventory 73/0/0. Fresh audit: **35 HIGH_COMPLEXITY** (was 36), no high-complexity finding in `app/runtime_orchestrator.py`; total **907** heuristic records across 217 files.

---
## APP_L v40 — RuntimeOrchestrator diagnostic observability

Runtime diagnostics now use module logging and report a broken optional sink as a warning instead of silently swallowing it; normal diagnostics stay non-fatal. Regression injects an `info()` failure, asserts the warning and cleanly stops the worker.

Приёмка: focused Runtime suite 2 PASS; `pytest tests/ -q` = **258 PASS**, compileall/AST OK, data inventory 73/0/0. Fresh audit: **325 BARE_PRINT** (was 326), **119 SILENT_EXCEPT_PASS** (was 120), neither selected record remains in `app/runtime_orchestrator.py`; total **905** heuristic records across 217 files.

---
## APP_L v40 — cancellable voice-onboarding recording

`record_step` now accepts an optional stop event: cancellation wakes the timed capture, finalizes the recorder, preserves partial diagnostic metadata but marks the step cancelled/non-accepted. Progress totals only accepted, non-cancelled steps, so partial recordings cannot advance RVC readiness. Existing callers remain compatible.

Приёмка: focused onboarding suite 2 PASS; `pytest tests/ -q` = **259 PASS**, compileall/AST OK, data inventory 73/0/0. Fresh audit: **7 BLOCKING_SLEEP** (was 8), none in `modules/voice_onboarding.py`; total **904** heuristic records across 218 files.

---
## APP_L v40 — BLOCKING_SLEEP semantic scope

Deep audit now retains unannotated production waits while excluding only AST-proven `_self_test` ranges, pytest files and audit support files. Regression proves a runtime sleep remains flagged and all three non-production classes do not. This is scope correction, not a blanket safety claim for sleeps.

Приёмка: focused deep-audit suite 8 PASS; `pytest tests/ -q` = **260 PASS**, compileall/AST OK, data inventory 73/0/0. Fresh audit: **0 BLOCKING_SLEEP**, HIGH_COMPLEXITY 35, LONG_FUNCTION 29, SILENT_EXCEPT_PASS 119, BARE_PRINT 325; **898** total heuristic records across 218 files.

---
## APP_L v40 — voice-recording failure observability

Real-time recorder callback, metrics and stream-shutdown failures remain non-fatal but now set inspectable `last_error` instead of being silently swallowed. Focused regressions force metrics and shutdown errors while preserving compatible fallback results; no microphone/device claim was made.

Приёмка: focused recorder suite 3 PASS; `pytest tests/ -q` = **262 PASS**, compileall/AST OK, data inventory 73/0/0. Fresh audit: **116 SILENT_EXCEPT_PASS** (was 119); two unrelated I/O fallbacks remain in `modules/voice_recording.py`; total **895** heuristic records across 219 files.

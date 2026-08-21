# PLAN_v39 — ШАГ 043: полный artist dossier pipeline

## Pipeline contract

`DossierManager._analyze_single_track()` сохраняет отдельный track record и выполняет стадии строго через `SequentialAIRunner`: **Demucs vocals → faster-whisper ASR → DSP (librosa/essentia) → CLAP tags → analysis_llm**. Каждая стадия сохраняет структурированный результат либо явную причину `skipped`/`error`; итог track JSON всегда находится в `data/artist_dossier/<artist>/tracks/`.

| Участок | Реализованное поведение |
|---|---|
| Локальный intake | `LocalFolderCollector` принимает audio и `.txt` lyrics, удаляет `<artist> - ` prefix из title и объединяет одноимённые audio/text entries. Это устраняет реальный CLI-разрыв: `--dossier-add <folder>` ранее игнорировал текстовые референсы. |
| Demucs | Берёт именно stem `vocals` по объявленному порядку `model.sources`; output проверяется на длительность и аудио-качество. |
| ASR | Использует vocals при наличии или original audio; transcript проходит content/repetition gate до записи. |
| DSP/CLAP | Сохраняются только проверенные BPM/key/RMS и unique tag subset; отсутствие модели возвращает явный `skipped`. |
| Track analysis | Требует `theme`, `storyline`, `key_lines`, `analysis`, `hook`, `reusable_elements`; без `analysis_llm` stage имеет `skipped_reason`, а track сохраняется как `partial`. |
| Artist aggregation | Требует `bio`, `themes`, `slang`, `flow`, `analogs`; normalization добавляет совместимые `core_themes`/`lexicon` aliases для downstream prompts. Prompt явно запрещает выдумывать биографические факты. |

## Runtime data boundary

`data/artist_dossier/` является пользовательским/runtime output, а не versioned fixture-каталогом. Поэтому versioned data inventory намеренно не считает его неизвестным asset; это не отключает аудит остальных `data/` файлов.

## Evidence

Добавлены/усилены регрессии rich artist/track schema, fake `analysis_llm` aggregation с compatibility aliases, `LocalFolderCollector` audio+lyrics merge и deferred dossier с проверкой `analysis_llm unavailable` в stage report. Сквозной CLI smoke `--dossier-add` с local `.txt` теперь добавляет **1** track, а `--dossier-build` возвращает честный `analysis_llm unavailable - dossier deferred` с `tracks_count=1` в sandbox.

На момент приёмки: `pytest tests/test_ai_layer.py -q` — **31 passed**; `pytest tests/ -q` — **108 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.

> Demucs, faster-whisper, CLAP и analysis_llm weights отсутствуют в sandbox. Их real inference не заявляется выполненным: проверены последовательный lifecycle, fake-handle contracts, persistence, quality gates и честные unavailable/deferred outcomes.

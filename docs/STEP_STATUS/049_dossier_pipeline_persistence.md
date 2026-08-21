# PLAN_v39 — ШАГ 049: persistence ASR, Demucs, tags и DSP в досье

`DossierManager` уже исполнял последовательные роли Demucs → ASR → DSP → CLAP → LLM, однако successful intermediary outputs оставались только в transient runner sink. Исправлено сохранение итоговых track features: `stems.vocals`, `stem_source_index` и `transcript_path` теперь persist в `tracks/<track_id>.json`; DSP fields (BPM, key, duration, RMS) и CLAP tags сохранялись ранее и остаются частью того же record.

| Роль | Persisted track data | Нет модели |
|---|---|---|
| Demucs | `stems.vocals`, `stem_source_index` | `skipped` с reason |
| faster-whisper | lyrics и `transcript_path` | `skipped` с reason |
| DSP | BPM, key, duration, RMS | `skipped` с reason |
| CLAP | validated tags | `skipped` с reason |

На момент приёмки: `pytest tests/ -q` — **116 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**. Heavy Demucs/faster-whisper/CLAP weights отсутствуют в sandbox, поэтому production inference честно **BLOCKED**; persistence contract реализован и не теряет валидные outputs при доступных handles.

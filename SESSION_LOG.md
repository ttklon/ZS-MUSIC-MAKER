
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

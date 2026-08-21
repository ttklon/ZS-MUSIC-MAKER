# PROJECT_STATE — ZS Music Maker

> **Канонический snapshot:** v39.9.0, PLAN_v39 ШАГ 069. Этот файл фиксирует состояние versioned дерева на момент приёмки; воспроизводимый источник матрицы — `python tools/readiness.py --inventory-markdown`.
>
> **Метод:** Git перечисляет только versioned `.py` в `main.py`, `app/`, `agents/`, `modules/`, `tools/`, `ui/`, `updater/`. Для каждого файла readiness проверяет AST syntax и статические references в production/test sources. Он **не запускает** optional model weights и не переводит absence dependency в успех.

## Сводка фактической инвентаризации

| Показатель | Значение |
|---|---:|
| Versioned production Python modules | 147 |
| `REAL_PASS` — parseable с production или test static signal | 140 |
| `REAL_FAIL` — syntax error | 0 |
| `PLANNED` — parseable, без static signal | 7 |
| Versioned test files | 26 |
| Полный pytest suite на приёмке | 141 passed |
| AST dead imports на приёмке | 0 |

> `REAL_PASS` в этой matrix означает **статически проверяемую связность**, а не утверждение о real AI inference. Runtime с optional packages/weights имеет отдельные честные статусы ниже.

## Runtime и acceptance status

| Область | Статус | Основание и граница |
|---|---|---|
| Core CLI, orchestrators, adapters | REAL_PASS (static) | Parseable/import-referenced inventory, pytest coverage; фактические команды проходят отдельные regression tests. |
| Audio core (librosa + soundfile) | REAL_PASS | В среде доступны `librosa` и `soundfile`; audio tests выполняются. |
| MusicGen, Demucs, Matchering, Pedalboard, pyloudnorm | BLOCKED | Optional runtime packages отсутствуют в sandbox; adapters/gates и fake-handle contracts тестируются, но real engine run не заявляется. |
| XTTS/RVC/SDXL/CLAP/ASR/LLM weights | BLOCKED | Нет соответствующих heavy runtime/weights; pipeline фиксирует skipped/fallback, не fake-success. |
| AI sequential runner / manifest / quality gates | REAL_PASS (contract) | Regression suite покрывает timeout/OOM lifecycle, artifact validation и manifest contracts. |
| Windows EXE build / desktop GUI | NOT_TESTED | Выполняется только Windows GitHub runner/целевой Windows host. Build workflow хранит artifact 30 дней; `v*` tag release job не исполнялся в sandbox. |
| Release export | REAL_PASS (contract) | ZIP/fingerprint tests существуют; external store/distribution не выполнялись. |

## Формальная matrix versioned модулей

Следующая таблица сгенерирована при приёмке командой `python tools/readiness.py --inventory-markdown`. При изменении production `.py` её необходимо регенерировать в том же коммите; число строк должно совпадать с `tracked_modules` в обычном `python tools/readiness.py` JSON.

| Versioned module | Status | AST syntax | Production refs | Test refs |
|---|---|---:|---:|---:|
| agents/__init__.py | REAL_PASS | PASS | 76 | 14 |
| agents/sample_hunter.py | REAL_PASS | PASS | 21 | 0 |
| agents/sample_hunter_v9.py | REAL_PASS | PASS | 10 | 0 |
| agents/training_texts.py | PLANNED | PASS | 0 | 0 |
| agents/trend_scout.py | REAL_PASS | PASS | 9 | 0 |
| agents/trend_scout_v3.py | REAL_PASS | PASS | 7 | 0 |
| app/__init__.py | REAL_PASS | PASS | 76 | 14 |
| app/ai/__init__.py | REAL_PASS | PASS | 76 | 14 |
| app/ai/llm_service.py | REAL_PASS | PASS | 3 | 0 |
| app/ai/prompts.py | REAL_PASS | PASS | 17 | 4 |
| app/ai/quality.py | REAL_PASS | PASS | 190 | 87 |
| app/ai/registry.py | REAL_PASS | PASS | 82 | 28 |
| app/ai/sequential_runner.py | REAL_PASS | PASS | 5 | 12 |
| app/core/__init__.py | REAL_PASS | PASS | 76 | 14 |
| app/core/cover_gen.py | REAL_PASS | PASS | 4 | 0 |
| app/core/font_utils.py | REAL_PASS | PASS | 11 | 2 |
| app/core/hw_autodetect.py | REAL_PASS | PASS | 18 | 0 |
| app/core/isrc.py | REAL_PASS | PASS | 76 | 38 |
| app/core/license_manager.py | REAL_PASS | PASS | 8 | 0 |
| app/core/logger.py | REAL_PASS | PASS | 74 | 0 |
| app/core/model_manager.py | REAL_PASS | PASS | 2 | 0 |
| app/core/musicgen_texture.py | REAL_PASS | PASS | 17 | 0 |
| app/core/orchestrator.py | REAL_PASS | PASS | 109 | 30 |
| app/core/orchestrator_ai.py | REAL_PASS | PASS | 11 | 22 |
| app/core/orchestrator_async.py | REAL_PASS | PASS | 2 | 0 |
| app/core/orchestrator_god.py | REAL_PASS | PASS | 10 | 0 |
| app/core/orchestrator_v10_patch.py | REAL_PASS | PASS | 2 | 0 |
| app/core/orchestrator_v11_patch.py | REAL_PASS | PASS | 9 | 0 |
| app/core/orchestrator_v12_patch.py | REAL_PASS | PASS | 7 | 0 |
| app/core/orchestrator_v8_patch.py | REAL_PASS | PASS | 3 | 0 |
| app/core/orchestrator_v9_patch.py | REAL_PASS | PASS | 3 | 0 |
| app/core/pipeline_core.py | REAL_PASS | PASS | 2 | 2 |
| app/core/security_utils.py | REAL_PASS | PASS | 8 | 2 |
| app/gui/__init__.py | REAL_PASS | PASS | 76 | 14 |
| app/gui/onboarding.py | REAL_PASS | PASS | 40 | 0 |
| app/gui/theme.py | REAL_PASS | PASS | 152 | 15 |
| app/gui/theme_v12.py | REAL_PASS | PASS | 3 | 0 |
| app/gui/wizard.py | REAL_PASS | PASS | 179 | 1 |
| app/gui/wizard_v8_extensions.py | PLANNED | PASS | 0 | 0 |
| app/hw_probe.py | REAL_PASS | PASS | 6 | 0 |
| app/logger.py | REAL_PASS | PASS | 72 | 0 |
| app/plugins/advanced.py | REAL_PASS | PASS | 6 | 0 |
| app/plugins/base.py | REAL_PASS | PASS | 120 | 11 |
| app/runtime_orchestrator.py | REAL_PASS | PASS | 1 | 0 |
| app/version_info.py | REAL_PASS | PASS | 2 | 3 |
| main.py | REAL_PASS | PASS | 493 | 64 |
| modules/__init__.py | REAL_PASS | PASS | 76 | 14 |
| modules/ai_arranger.py | REAL_PASS | PASS | 2 | 0 |
| modules/ai_detector_pro.py | REAL_PASS | PASS | 4 | 2 |
| modules/analyzer.py | REAL_PASS | PASS | 19 | 0 |
| modules/anti_ai_polish.py | REAL_PASS | PASS | 15 | 0 |
| modules/anti_neuro_v10.py | REAL_PASS | PASS | 20 | 4 |
| modules/arrangement_engine.py | REAL_PASS | PASS | 13 | 0 |
| modules/artist_dossier/__init__.py | REAL_PASS | PASS | 76 | 14 |
| modules/artist_dossier/collectors.py | REAL_PASS | PASS | 2 | 2 |
| modules/artist_dossier/manager.py | REAL_PASS | PASS | 48 | 23 |
| modules/author_ref_lyrics.py | REAL_PASS | PASS | 20 | 0 |
| modules/auto_qa.py | REAL_PASS | PASS | 16 | 0 |
| modules/beat_constructor.py | REAL_PASS | PASS | 25 | 4 |
| modules/beat_gen.py | REAL_PASS | PASS | 5 | 6 |
| modules/beat_gen_ai.py | REAL_PASS | PASS | 1 | 6 |
| modules/chanson_engine.py | REAL_PASS | PASS | 1 | 0 |
| modules/cover_art_ai.py | REAL_PASS | PASS | 2 | 9 |
| modules/cover_art_gen.py | REAL_PASS | PASS | 8 | 0 |
| modules/cyber_synth.py | REAL_PASS | PASS | 4 | 0 |
| modules/distribution_export_v11.py | REAL_PASS | PASS | 15 | 0 |
| modules/essentia_analyzer.py | REAL_PASS | PASS | 3 | 0 |
| modules/expert_mode_v11.py | REAL_PASS | PASS | 9 | 0 |
| modules/female_backing.py | REAL_PASS | PASS | 33 | 0 |
| modules/freesound_client.py | REAL_PASS | PASS | 3 | 0 |
| modules/genre_engine.py | REAL_PASS | PASS | 9 | 0 |
| modules/genre_expansion_100.py | REAL_PASS | PASS | 0 | 2 |
| modules/global_audit_fixer.py | REAL_PASS | PASS | 0 | 2 |
| modules/groove_extractor.py | REAL_PASS | PASS | 16 | 0 |
| modules/health_v12.py | REAL_PASS | PASS | 32 | 0 |
| modules/hit_kpi_monitor_v11.py | REAL_PASS | PASS | 14 | 0 |
| modules/hit_scorer.py | REAL_PASS | PASS | 40 | 6 |
| modules/hw_directml.py | REAL_PASS | PASS | 9 | 0 |
| modules/karaoke_engine.py | REAL_PASS | PASS | 5 | 0 |
| modules/kpi_dashboard_v12.py | REAL_PASS | PASS | 18 | 0 |
| modules/llm_clients_v15.py | REAL_PASS | PASS | 3 | 0 |
| modules/lyric_vault_v10.py | REAL_PASS | PASS | 6 | 0 |
| modules/lyrics_gen.py | REAL_PASS | PASS | 29 | 7 |
| modules/lyrics_gen_ai.py | REAL_PASS | PASS | 2 | 0 |
| modules/lyrics_gen_v8.py | REAL_PASS | PASS | 7 | 0 |
| modules/master_pipeline_v12.py | REAL_PASS | PASS | 24 | 0 |
| modules/mastering.py | REAL_PASS | PASS | 151 | 15 |
| modules/mastering_ai.py | REAL_PASS | PASS | 9 | 9 |
| modules/mastering_pro.py | REAL_PASS | PASS | 26 | 0 |
| modules/mastering_v9.py | REAL_PASS | PASS | 10 | 0 |
| modules/matchering_master.py | REAL_PASS | PASS | 10 | 0 |
| modules/midi_generator.py | REAL_PASS | PASS | 16 | 0 |
| modules/mixdown.py | REAL_PASS | PASS | 20 | 0 |
| modules/musical_intelligence.py | REAL_PASS | PASS | 2 | 0 |
| modules/onboarding_tour.py | REAL_PASS | PASS | 6 | 0 |
| modules/phoneme_coverage.py | REAL_PASS | PASS | 15 | 0 |
| modules/phonk_engine.py | REAL_PASS | PASS | 4 | 2 |
| modules/phonk_engine_v2.py | PLANNED | PASS | 0 | 0 |
| modules/presets.py | REAL_PASS | PASS | 37 | 6 |
| modules/pro_audio_dsp.py | REAL_PASS | PASS | 0 | 4 |
| modules/provenance.py | REAL_PASS | PASS | 15 | 0 |
| modules/reference_ingest.py | REAL_PASS | PASS | 14 | 0 |
| modules/release_export.py | REAL_PASS | PASS | 11 | 6 |
| modules/release_pack_full.py | REAL_PASS | PASS | 5 | 0 |
| modules/release_pack_v9.py | REAL_PASS | PASS | 15 | 0 |
| modules/remix.py | REAL_PASS | PASS | 4 | 8 |
| modules/render_queue.py | REAL_PASS | PASS | 9 | 6 |
| modules/rvc_manager.py | REAL_PASS | PASS | 36 | 0 |
| modules/rvc_trainer_v9.py | REAL_PASS | PASS | 12 | 2 |
| modules/self_diag_v13.py | REAL_PASS | PASS | 8 | 0 |
| modules/sidechain.py | REAL_PASS | PASS | 30 | 0 |
| modules/stem_splitter.py | REAL_PASS | PASS | 17 | 2 |
| modules/tiktok_edit_v9.py | REAL_PASS | PASS | 8 | 0 |
| modules/track_templates.py | REAL_PASS | PASS | 7 | 0 |
| modules/user_profile.py | REAL_PASS | PASS | 15 | 0 |
| modules/video_edit_v11.py | REAL_PASS | PASS | 20 | 0 |
| modules/vocal_fx.py | REAL_PASS | PASS | 12 | 0 |
| modules/voice_cleaner.py | REAL_PASS | PASS | 4 | 0 |
| modules/voice_convert.py | REAL_PASS | PASS | 19 | 0 |
| modules/voice_onboarding.py | REAL_PASS | PASS | 8 | 0 |
| modules/voice_recording.py | REAL_PASS | PASS | 7 | 0 |
| modules/voice_synth.py | REAL_PASS | PASS | 37 | 10 |
| modules/voice_synth_ai.py | REAL_PASS | PASS | 1 | 3 |
| modules/voice_vault_v9.py | REAL_PASS | PASS | 17 | 2 |
| modules/wizard_v12_integration.py | REAL_PASS | PASS | 3 | 0 |
| tools/__init__.py | REAL_PASS | PASS | 76 | 14 |
| tools/ab_compare.py | REAL_PASS | PASS | 3 | 0 |
| tools/ast_dead_imports.py | REAL_PASS | PASS | 3 | 2 |
| tools/audit_data_inventory.py | REAL_PASS | PASS | 1 | 2 |
| tools/deep_audit_v40.py | REAL_PASS | PASS | 2 | 0 |
| tools/deep_audit_v40_expand.py | PLANNED | PASS | 0 | 0 |
| tools/deep_audit_v40_report.py | PLANNED | PASS | 0 | 0 |
| tools/fallback_audit.py | REAL_PASS | PASS | 7 | 0 |
| tools/genre_validator.py | REAL_PASS | PASS | 0 | 2 |
| tools/lazy_dirs_patch.py | PLANNED | PASS | 0 | 0 |
| tools/p0_truth_test.py | PLANNED | PASS | 0 | 0 |
| tools/pull_ai_models.py | REAL_PASS | PASS | 6 | 1 |
| tools/readiness.py | REAL_PASS | PASS | 20 | 13 |
| tools/real_e2e_v14.py | REAL_PASS | PASS | 5 | 0 |
| tools/smoke_v26.py | REAL_PASS | PASS | 22 | 0 |
| tools/smoke_v29.py | REAL_PASS | PASS | 24 | 0 |
| tools/validate_final_track.py | REAL_PASS | PASS | 1 | 0 |
| ui/__init__.py | REAL_PASS | PASS | 76 | 14 |
| ui/karaoke_recorder.py | REAL_PASS | PASS | 4 | 0 |
| ui/tutorial.py | REAL_PASS | PASS | 22 | 0 |
| updater/__init__.py | REAL_PASS | PASS | 76 | 14 |
| updater/updater.py | REAL_PASS | PASS | 29 | 3 |

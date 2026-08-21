================================================================================
APP_B. КАРТОЧКИ МОДУЛЕЙ (каждый .py файл репозитория)
================================================================================

##### МОДУЛЬ agents/__init__.py (2 LOC)
------------------------------------------------------------
  Функции: —
  Классы: —
  Неиспользуемые импорты: sample_hunter@2, training_texts@2, trend_scout@2
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ agents/sample_hunter.py (205 LOC)
------------------------------------------------------------
  Функции: list_local, search_wikimedia, search_freesound_public, search_pixabay, search_online, hunt, download_to_cache
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ agents/sample_hunter_v9.py (367 LOC)
------------------------------------------------------------
  Функции: plan_queries, list_local, _http_get, search_freesound_web, search_wikimedia, search_archive_org, _license_gate, search_online, unified_search, save_manifest
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ agents/training_texts.py (140 LOC)
------------------------------------------------------------
  Функции: get_next_text, _styles_remaining, _instruction, all_styles, progress_summary
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ agents/trend_scout.py (156 LOC)
------------------------------------------------------------
  Функции: scout_trends, _duckduckgo_search, _fallback_trends, _load_cache, _save_cache, get_hot_topics
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ agents/trend_scout_v3.py (247 LOC)
------------------------------------------------------------
  Функции: _load_cache, _save_cache, _ddg, _reddit_hot, scout, actual_slang_for_prompt
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/__init__.py (3 LOC)
------------------------------------------------------------
  Функции: —
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/ai/__init__.py (5 LOC)
------------------------------------------------------------
  Функции: —
  Классы: —
  Неиспользуемые импорты: AIStage@5, HardwareBudget@4, MODEL_REGISTRY@4
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/ai/llm_service.py (45 LOC)
------------------------------------------------------------
  Функции: complete, complete_json
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/ai/prompts.py (94 LOC)
------------------------------------------------------------
  Функции: build_lyrics_prompt, build_dossier_prompt, build_track_dossier_prompt, build_metadata_prompt, build_music_prompt, build_cover_prompt
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/ai/registry.py (365 LOC)
------------------------------------------------------------
  Функции: from_env, __init__, status, is_available, load, unload, use, pick_device, _register_default_loaders, __init__, __enter__, __exit__, _llama, _musicgen
  Классы: HardwareBudget, LoadedModel, ModelRegistry, _UseCtx
  Неиспользуемые импорты: audiocraft@141, torch_directml@238, transformers@156
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/ai/sequential_runner.py (134 LOC)
------------------------------------------------------------
  Функции: _summarize, to_dict, __init__, add, sink, run
  Классы: AIStage, StageReport, RunReport, SequentialAIRunner
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/core/__init__.py (0 LOC)
------------------------------------------------------------
  Функции: —
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/core/cover_gen.py (59 LOC)
------------------------------------------------------------
  Функции: make_cover, _get_font
  Классы: —
  Неиспользуемые импорты: hashlib@5
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/core/hw_autodetect.py (212 LOC)
------------------------------------------------------------
  Функции: _cpu_info, _gpu_info, detect, _recommendations, human_summary
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/core/license_manager.py (66 LOC)
------------------------------------------------------------
  Функции: normalize, is_free_commercial, check
  Классы: LicenseCheck
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/core/logger.py (44 LOC)
------------------------------------------------------------
  Функции: setup_logger
  Классы: —
  Неиспользуемые импорты: os@10
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/core/model_manager.py (64 LOC)
------------------------------------------------------------
  Функции: __init__, ensure_model, load_torch_model
  Классы: ModelManager
  Неиспользуемые импорты: logging@10, os@9, safe_hash@12
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/core/musicgen_texture.py (261 LOC)
------------------------------------------------------------
  Функции: choose_size, _load_musicgen, unload_all, detect_availability, get_status, _cache_key, generate_texture, generate_batch, _pink_noise_fallback, generate_atmosphere, generate_fx_hits
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/core/orchestrator.py (2037 LOC)
------------------------------------------------------------
  Функции: _timed, _is_simulation_result, _is_blocked_result, _normalize_path_map, _default_style_for_genre, _stage_analyze, _stage_groove, _stage_arrangement, _stage_beat, _synth_beat, _texture_scaffold, _stage_texture, _text_to_struct, _struct_to_text
  Классы: PipelineStage, PipelineResult
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/core/orchestrator_ai.py (293 LOC)
------------------------------------------------------------
  Функции: _slug, run_ai_pipeline, stage_hw, stage_dossier_load, stage_lyrics, stage_metadata, stage_music, stage_vocal, stage_rvc, stage_mix, stage_master, stage_cover, stage_tag
  Классы: —
  Неиспользуемые импорты: Any@6, Dict@6, Optional@6
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/core/orchestrator_async.py (118 LOC)
------------------------------------------------------------
  Функции: run_stage_async, main_async, __init__, _run_limited, run_pipeline
  Классы: AsyncStage, AsyncOrchestrator
  Неиспользуемые импорты: Dict@14
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/core/orchestrator_god.py (229 LOC)
------------------------------------------------------------
  Функции: _json_safe, _save_project_meta, run_god_pipeline, stage_arr, stage_midi, stage_audio, stage_vocal, stage_master
  Классы: —
  Неиспользуемые импорты: Dict@13, List@13, app_logger@16, time@10
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/core/orchestrator_v10_patch.py (226 LOC)
------------------------------------------------------------
  Функции: apply_v10_patch, full_v10_pipeline
  Классы: Dummy
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/core/orchestrator_v11_patch.py (401 LOC)
------------------------------------------------------------
  Функции: _safe_print, _load_deps, run_full_pipeline_v11, _minimal_pipeline_fallback, register, _self_test, prog
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/core/orchestrator_v12_patch.py (144 LOC)
------------------------------------------------------------
  Функции: _safe_print, run_full_pipeline_v12, register
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/core/orchestrator_v8_patch.py (136 LOC)
------------------------------------------------------------
  Функции: _stage, run_pipeline_v8, apply
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/core/orchestrator_v9_patch.py (284 LOC)
------------------------------------------------------------
  Функции: _stage, run_pipeline_v9, apply, _wrapper
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/core/pipeline_core.py (132 LOC)
------------------------------------------------------------
  Функции: __init__, execute, __init__, add_stage, _save_checkpoint, run
  Классы: StageResult, PipelineContext, PipelineStage, ZSPipeline
  Неиспользуемые импорты: pickle@13
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/core/security_utils.py (52 LOC)
------------------------------------------------------------
  Функции: safe_hash, download_file, get_json
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/gui/__init__.py (0 LOC)
------------------------------------------------------------
  Функции: —
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/gui/onboarding.py (236 LOC)
------------------------------------------------------------
  Функции: maybe_show_onboarding, show_help_tour, __init__, render, prev, next
  Классы: OnboardingDialog
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/gui/theme.py (41 LOC)
------------------------------------------------------------
  Функции: apply_dark
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/gui/theme_v12.py (261 LOC)
------------------------------------------------------------
  Функции: qss, apply
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/gui/wizard.py (1042 LOC)
------------------------------------------------------------
  Функции: H1, H2, DIM, HR, __init__, enter, commit, help_text, __init__, enter, commit, help_text, __init__, dragEnterEvent
  Классы: StepBase, StepArtist, StepReferences, StepPreset, StepSamples, StepLyrics, StepVoice, StepExpert
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/gui/wizard_v8_extensions.py (350 LOC)
------------------------------------------------------------
  Функции: __init__, _refresh_authors, _on_scan, _on_fetch, selected_author, __init__, is_enabled, placement, _preview, __init__, refresh, __init__, set_report, __init__
  Классы: AuthorPickerPanel, FemaleBackingPanel, QualityBadge, AutoQAResultPanel, TemplateManagerDialog
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/hw_probe.py (65 LOC)
------------------------------------------------------------
  Функции: probe, main
  Классы: HW
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/logger.py (43 LOC)
------------------------------------------------------------
  Функции: setup_logger, __init__, write, flush
  Классы: SafeStream
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/plugins/advanced.py (86 LOC)
------------------------------------------------------------
  Функции: __init__, process, __init__, __init__, process, __init__, __init__, __call__, __init__, __call__
  Классы: PedalboardPlugin, PhonkDistortion, AntiAINeuroObfuscator, _NoopFx, Pedalboard, Compose
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/plugins/base.py (86 LOC)
------------------------------------------------------------
  Функции: __init__, process, __repr__, __init__, add, process, __new__, discover
  Классы: AudioPlugin, PluginChain, PluginRegistry
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ app/runtime_orchestrator.py (149 LOC)
------------------------------------------------------------
  Функции: __init__, _log, _ensure_worker, enqueue, enqueue_batch, _run_loop, _process
  Классы: Job, RuntimeOrchestrator
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ install.py (97 LOC)
------------------------------------------------------------
  Функции: run_cmd, setup
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ main.py (554 LOC)
------------------------------------------------------------
  Функции: _load_version_info, _setup_console_encoding, _safe_print, _header, _health_snapshot, _try_launch_gui_pyside, _try_launch_gui_gradio, _register_patches, _cli_smoke, _cli_dry_run, _cli_dashboard, _cli_self_diag, _cli_e2e, _cli_onboarding
  Классы: ProjectContext
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/__init__.py (2 LOC)
------------------------------------------------------------
  Функции: —
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/ai_arranger.py (54 LOC)
------------------------------------------------------------
  Функции: __init__, get_structure
  Классы: AIArranger
  Неиспользуемые импорты: random@10
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/ai_detector_pro.py (190 LOC)
------------------------------------------------------------
  Функции: analyze_track
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/analyzer.py (257 LOC)
------------------------------------------------------------
  Функции: _safe_load, analyze_single, _infer_vibe, _bpm_range, analyze_multi, _save_to_vault, list_cached_analyses
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/anti_ai_polish.py (317 LOC)
------------------------------------------------------------
  Функции: _read, _write, _micro_timing_jitter, _breath_insert, _section_dynamics_variation, _ghost_harmonies_kill, _formulaic_structure_bust, _tape_saturation, _imperfect_tuning, _lofi_pass, polish_track
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/anti_neuro_v10.py (401 LOC)
------------------------------------------------------------
  Функции: polish_vocal, apply_polish, _polish_numpy, _apply_stage, capability_report
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/arrangement_engine.py (325 LOC)
------------------------------------------------------------
  Функции: _pick, _bars_to_seconds, _clamp, build_arrangement, _guess_genre, save_plan
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/artist_dossier/__init__.py (4 LOC)
------------------------------------------------------------
  Функции: —
  Классы: —
  Неиспользуемые импорты: DossierManager@4
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/artist_dossier/collectors.py (96 LOC)
------------------------------------------------------------
  Функции: __init__, collect, __init__, collect, __init__, collect, __init__, collect
  Классы: LocalFolderCollector, LyricVaultCollector, GeniusCollector, YouTubeCollector
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/artist_dossier/manager.py (318 LOC)
------------------------------------------------------------
  Функции: _slug, _track_id, __init__, add_artist, add_track, build_full_dossier, _analyze_single_track, _aggregate_artist_dossier, get_artist_dossier, get_track_dossier, list_artists, list_tracks, _save_artist, _load_artist
  Классы: TrackEntry, ArtistEntry, DossierManager
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/author_ref_lyrics.py (369 LOC)
------------------------------------------------------------
  Функции: _tokenize, _syllables_ru, _load_index, _save_index, ingest_lyrics_file, ingest_lyrics_text, ingest_reference_audio, build_style_profile, get_style_profile, search_author_online, fetch_and_ingest_author, build_style_prompt, scan_library, list_authors
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/auto_qa.py (204 LOC)
------------------------------------------------------------
  Функции: _loudness, _structure_check, audit_track, should_retry
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/beat_constructor.py (637 LOC)
------------------------------------------------------------
  Функции: construct_beat, __init__, _classify_samples, _load_audio, _generate_kick, _generate_snare, _generate_hihat, _generate_bass_line, _generate_melody, _generate_fx, _pan_audio, _build_section, build_track
  Классы: BeatConstructor
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/beat_gen.py (153 LOC)
------------------------------------------------------------
  Функции: _pick_device, _load_model, build_prompt, generate_texture, generate_beat, generate_from_samples
  Классы: —
  Неиспользуемые импорты: torch_directml@25
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/beat_gen_ai.py (52 LOC)
------------------------------------------------------------
  Функции: render_beat_ai
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/chanson_engine.py (195 LOC)
------------------------------------------------------------
  Функции: __init__, generate_kick, generate_snare, generate_hihat, generate_guitar_chord, synthesize_chanson_track
  Классы: ChansonEngine
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/cover_art_ai.py (32 LOC)
------------------------------------------------------------
  Функции: render_cover_ai
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/cover_art_gen.py (258 LOC)
------------------------------------------------------------
  Функции: generate, _fill_gradient, _apply_glitch, _apply_neon_grid, _apply_sun, _apply_chrome, _load_font, _center_text, _wrap_title, _contrast
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: C:\
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/cyber_synth.py (134 LOC)
------------------------------------------------------------
  Функции: __init__, generate_sub_bass, generate_cyber_lead, synthesize_track, sub_bass_pattern
  Классы: CyberSynth
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/distribution_export_v11.py (462 LOC)
------------------------------------------------------------
  Функции: _safe_print, _copy_safe, build_spotify_package, build_yandex_vk_package, build_tiktok_package, build_youtube_package, build_shazam_package, build_all_distribution_packages, _self_test, ensure, existing
  Классы: TrackMetadata, ReleaseFiles
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/essentia_analyzer.py (172 LOC)
------------------------------------------------------------
  Функции: analyze_advanced, _analyze_essentia, _analyze_librosa_fallback, save_report
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/expert_mode_v11.py (324 LOC)
------------------------------------------------------------
  Функции: _safe_print, validate, preset_default, preset_phonk_car, preset_hyperpop_tiktok, preset_trap_summer, apply_preset, merge_with_wizard_state, _self_test, to_flat_dict, to_dict, save, load, from_dict
  Классы: ExpertBeat, ExpertLyrics, ExpertVoice, ExpertMix, ExpertMaster, ExpertMusicGen, ExpertAntiNeuro, ExpertRender
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/female_backing.py (225 LOC)
------------------------------------------------------------
  Функции: _synth_silero, _synth_bark, _synth_pyttsx, synth_female_line, sweeten_backing, make_chorus_backing, mix_backing_into_vocal
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/freesound_client.py (200 LOC)
------------------------------------------------------------
  Функции: _load_key, search, _offline_search, download_preview, _append_manifest
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/genre_engine.py (127 LOC)
------------------------------------------------------------
  Функции: __new__, __init__, _load_defaults, register, get_profile, list_genres, __init__, create_wizard_state
  Классы: GenreProfile, StyleRegistry, GenreFactory
  Неиспользуемые импорты: Any@11, Optional@11
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/genre_expansion_100.py (98 LOC)
------------------------------------------------------------
  Функции: get_genre_profile, list_all_supported_genres
  Классы: —
  Неиспользуемые импорты: json@7
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/global_audit_fixer.py (37 LOC)
------------------------------------------------------------
  Функции: audit_system_integrity
  Классы: —
  Неиспользуемые импорты: os@7, sys@8
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/groove_extractor.py (234 LOC)
------------------------------------------------------------
  Функции: extract_groove, merge_grooves
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/health_v12.py (381 LOC)
------------------------------------------------------------
  Функции: _probe, _hw_probe, _advice_for, collect, _fmt_row, main, as_dict, as_dict
  Классы: ProbeResult, HealthReport
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/hit_kpi_monitor_v11.py (349 LOC)
------------------------------------------------------------
  Функции: _safe_print, check_release_completeness, check_ai_detector, finalize_session, render_kpi_report_md, latest_sessions, _self_test, duration_min, pipeline_min, start_stage, end_stage, to_dict
  Классы: KpiStage, KpiSession
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/hit_scorer.py (588 LOC)
------------------------------------------------------------
  Функции: _load_audio, _rms, _db, _hook_energy, _hook_repeatability, _chorus_catchiness, _drop_impact, _tiktok_hookability, _bpm_dance_fitness, _loudness_lufs, _stereo_width, _low_end_power, _vocal_presence, _structure_clarity
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/hw_directml.py (145 LOC)
------------------------------------------------------------
  Функции: detect, _wmic_vram_mb, save_profile, choose_musicgen_variant
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/karaoke_engine.py (191 LOC)
------------------------------------------------------------
  Функции: make_wordmap_from_lyrics, score_take, __init__, on, _fire, elapsed_ms, current_word, start, stop, _run
  Классы: KaraokeSession
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/kpi_dashboard_v12.py (411 LOC)
------------------------------------------------------------
  Функции: _load_json, _newest, _health_section, _pipeline_section, _smoke_section, _tz_percent, build, render_markdown, render_text, main, as_dict, has
  Классы: DashboardSection, Dashboard
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/llm_clients_v15.py (580 LOC)
------------------------------------------------------------
  Функции: _derive_key, save_secrets, load_secrets, get_keys_from_env, call_ollama, call_openrouter, call_grok, call_gemini, local_fallback_lyrics, _cli, __init__, to_dict, __init__, _preflight
  Классы: ProviderResult, LLMRouter
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/lyric_vault_v10.py (252 LOC)
------------------------------------------------------------
  Функции: _syllable_count, add_line, load_all, find_lines, mark_used, rebuild_index, export_lrc, _recently_used_ids, _load_usage, _save_usage
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/lyrics_gen.py (310 LOC)
------------------------------------------------------------
  Функции: _load_lyric_memory, _save_lyric_memory, _pick_punches, _try_ollama, _template_verse, _template_hook_en, _is_english, generate_lyrics, get_lyric_memory
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/lyrics_gen_ai.py (57 LOC)
------------------------------------------------------------
  Функции: generate_lyrics_ai
  Классы: —
  Неиспользуемые импорты: Optional@6
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/lyrics_gen_v8.py (196 LOC)
------------------------------------------------------------
  Функции: _split_blocks, _validate_rhythm, generate_lyrics_v8
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/master_pipeline_v12.py (719 LOC)
------------------------------------------------------------
  Функции: _log, _jsonable, _stage, _try_import, run_master_pipeline, _make_human_summary, _finalize, run, _demo, as_dict, as_dict, progress, _do_ri, _do_sh
  Классы: StageResult, MasterResult
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/mastering.py (210 LOC)
------------------------------------------------------------
  Функции: _one_pole_shelf, _apply_stand_eq, _loudness_dbfs, _loudness_lufs, _tanh_limit, _try_numpy_dsp, master_one, master_all_stands
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/mastering_ai.py (34 LOC)
------------------------------------------------------------
  Функции: master_ai
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/mastering_pro.py (188 LOC)
------------------------------------------------------------
  Функции: _sanitize, _apply_ceiling, process_mastering
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/mastering_v9.py (281 LOC)
------------------------------------------------------------
  Функции: _read, _write, _rms, measure, _apply_gain, _soft_limit, _eq_shelf, _widen_stereo, render_stand, render_all_stands, match_to_reference
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/matchering_master.py (133 LOC)
------------------------------------------------------------
  Функции: match_to_reference, master_to_stand, master_all_stands, _pydub_fallback
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/midi_generator.py (204 LOC)
------------------------------------------------------------
  Функции: __init__, _ensure_dir, get_status, generate_drum_pattern, generate_melody_pattern
  Классы: MIDIGenerator
  Неиспользуемые импорты: Optional@25
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/mixdown.py (177 LOC)
------------------------------------------------------------
  Функции: mix_beat_and_vocal, apply_eq, master_with_matchering, master_with_matchering_status, full_mixdown
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/musical_intelligence.py (91 LOC)
------------------------------------------------------------
  Функции: __init__, analyze_key, suggest_chords
  Классы: MusicalIntelligence
  Неиспользуемые импорты: aT@14, sf@11
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/onboarding_tour.py (213 LOC)
------------------------------------------------------------
  Функции: _tour_state_path, load_state, save_state, should_show, steps, get_step, mark_done, reset, run_console_demo
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/phoneme_coverage.py (137 LOC)
------------------------------------------------------------
  Функции: _collect_transcripts, compute_coverage, _make_suggestions
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/phonk_engine.py (13 LOC)
------------------------------------------------------------
  Функции: generate_cowbell
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/phonk_engine_v2.py (97 LOC)
------------------------------------------------------------
  Функции: __init__, generate_808, create_drift_track
  Классы: PhonkEngineV2
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/presets.py (170 LOC)
------------------------------------------------------------
  Функции: _load_all, list_presets, get_preset, save_user_preset, preset_to_style_vector
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/pro_audio_dsp.py (85 LOC)
------------------------------------------------------------
  Функции: align_stereo_phases, apply_mastering_chain
  Классы: ProAudioDSP
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/provenance.py (142 LOC)
------------------------------------------------------------
  Функции: _load, _save, add_sample, list_samples, check_commercial_safe, generate_attribution_text
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/reference_ingest.py (318 LOC)
------------------------------------------------------------
  Функции: _md5, _cache_path, _load_cached, _save_cached, _key_from_chroma, analyze_file, _consensus_bpm, _consensus_key, build_style_vector, _guess_genre, _guess_mood, _norm, _wavg
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/release_export.py (264 LOC)
------------------------------------------------------------
  Функции: _copy_or_convert, _write_id3, _write_flac_tags, export_release
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/release_pack_full.py (946 LOC)
------------------------------------------------------------
  Функции: _read_wav, _write_wav, _ensure_stereo, _hires_resample_48k, _make_cover, _lyrics_to_lrc, _lyrics_to_srt, _fake_stems, _instrumental_and_acapella, _find_hook, _make_clip, _distrokid_xml, _spotify_description, _youtube_description_html
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/release_pack_v9.py (180 LOC)
------------------------------------------------------------
  Функции: _safe_copy, _write_json, _readme_text, build_release_v9
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/render_queue.py (197 LOC)
------------------------------------------------------------
  Функции: _load_state, _save_state, to_dict, __init__, _restore, _persist, enqueue, enqueue_batch, status_summary, list_items, cancel, clear_done, start, stop
  Классы: QueueItem, RenderQueue
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/rvc_manager.py (481 LOC)
------------------------------------------------------------
  Функции: _load_state, _save_state, detect_backend, ensure_fork, infer, _fallback_pitch, get_state, is_trained, _p, __init__, on_progress, _emit, _dataset_ready, train
  Классы: RVCBackend, TrainingJob, RVCTrainer
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/rvc_trainer_v9.py (234 LOC)
------------------------------------------------------------
  Функции: _now, _mk_job_id, _save_job, _load_manifest, probe_backend, _build_plan, _run_training_bg, retrain_incremental, schedule_night_run, get_job, list_jobs
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/self_diag_v13.py (333 LOC)
------------------------------------------------------------
  Функции: _c, _read_json_silent, check_layout, check_health, check_kpi, check_smoke_recent, collect_action_plan, render_report, run, main_entry
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/sidechain.py (290 LOC)
------------------------------------------------------------
  Функции: _envelope_from_kick, _bandpass_numpy, _detect_kick_onsets, _numpy_dsp, measure_ducking_effect, apply_sidechain, capability_report
  Классы: SidechainResult
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/stem_splitter.py (75 LOC)
------------------------------------------------------------
  Функции: split_stems, analyze_arrangement
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/tiktok_edit_v9.py (267 LOC)
------------------------------------------------------------
  Функции: _read, _write, _find_hot_slice, _fade_in_out, cut_slice, make_all_cuts, _has_ffmpeg, make_vertical_video
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/track_templates.py (99 LOC)
------------------------------------------------------------
  Функции: _load_history, _save_history, save_template, list_templates, load_template, delete_template, push_history, get_history, clear_history
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/user_profile.py (157 LOC)
------------------------------------------------------------
  Функции: get_profile, save_profile, update, is_first_run, mark_onboarded, set_artist_name, get_artist_name, set_quality_mode, add_to_history, get_history, add_favorite_theme, add_favorite_preset, sync_voice_progress, save_last_settings
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/video_edit_v11.py (477 LOC)
------------------------------------------------------------
  Функции: _safe_print, _read_wav_mono, _rms_windows, detect_hook, _parse_lrc, _try_moviepy, _try_pil, _make_static_bg, _draw_title, build_video, _build_with_moviepy, _build_fallback, build_release_edits, _self_test
  Классы: VideoEditRequest, VideoEditResult
  Неиспользуемые импорты: нет
  Hardcoded пути: C:\
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/vocal_fx.py (370 LOC)
------------------------------------------------------------
  Функции: _read, _write, _resample_linear, _detune_cents, _fit_len, _rms_db, _find_phrase_ends, apply_vocal_double, apply_delay_throw, process_vocal, capability_report
  Классы: VocalFxResult
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/voice_cleaner.py (89 LOC)
------------------------------------------------------------
  Функции: _fallback_clean, clean_vocal
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/voice_convert.py (204 LOC)
------------------------------------------------------------
  Функции: _ensure_dirs, _load_index, _save_index, add_recording, vault_summary, rate_recording, train_rvc_model, incremental_finetune, get_training_status, convert, polish_vocal, polish_vocal_offline
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/voice_onboarding.py (274 LOC)
------------------------------------------------------------
  Функции: build_plan, compute_phoneme_coverage, _load_manifest, _save_manifest, record_step, compute_progress, is_ready_for_rvc, run_cli, as_dict, as_dict
  Классы: OnboardingStep, OnboardingProgress
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/voice_recording.py (395 LOC)
------------------------------------------------------------
  Функции: split_wav_into_takes, capability_report, as_dict, __init__, _callback, _emit_metrics, start, stop, _write_wav, ingest_wav, stop_and_split, _finalize
  Классы: RecorderMetrics, TakeInfo, RealMicRecorder
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/voice_synth.py (195 LOC)
------------------------------------------------------------
  Функции: _synth_silero, _synth_xtts, _synth_bark, _synth_pyttsx3, _synth_gtts, synth, _produced
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/voice_synth_ai.py (40 LOC)
------------------------------------------------------------
  Функции: synth_vocal_ai
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/voice_vault_v9.py (314 LOC)
------------------------------------------------------------
  Функции: _load_index, _save_index, _md5, _snr_and_clipping, _guess_style, _transcribe, calculate_phoneme_coverage, add_recording, list_recordings, clean_stats, export_manifest_for_rvc, maybe_trigger_retrain
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ modules/wizard_v12_integration.py (289 LOC)
------------------------------------------------------------
  Функции: _log, collect_wizard_state, bridge_wizard_to_v12, install_into_wizard_main, main_entry, as_dict, patched
  Классы: WizardBridgeResult
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ tests/test_ai_layer.py (88 LOC)
------------------------------------------------------------
  Функции: test_roles, test_status, test_essentia_avail, test_pure, test_skip, test_fallback, setUp, tearDown, test_add_list, test_dossier_deferred, test_dry
  Классы: TestRegistry, TestRunner, TestDossier, TestOrchestrator
  Неиспользуемые импорты: os@3
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ tests/test_audio_quality.py (70 LOC)
------------------------------------------------------------
  Функции: validate_audio_file, test_placeholder_audio_quality, test_clipping_detection
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ tests/test_genre_and_audit.py (33 LOC)
------------------------------------------------------------
  Функции: test_genre_expansion, test_audit_fixer
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ tests/test_mastering_results.py (43 LOC)
------------------------------------------------------------
  Функции: test_pro_mastering_quality_output
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ tests/test_pro_audio_dsp.py (49 LOC)
------------------------------------------------------------
  Функции: test_stereo_phase_alignment, test_mastering_chain
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ tools/__init__.py (1 LOC)
------------------------------------------------------------
  Функции: —
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ tools/ab_compare.py (236 LOC)
------------------------------------------------------------
  Функции: _load_stereo, _lufs, _true_peak_db, _stereo_width, _spectrogram, compare, _verdict, main
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ tools/fallback_audit.py (171 LOC)
------------------------------------------------------------
  Функции: _is_hard_refusal, scan_file, scan_all, main
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ tools/genre_validator.py (54 LOC)
------------------------------------------------------------
  Функции: validate_all
  Классы: —
  Неиспользуемые импорты: os@10
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ tools/lazy_dirs_patch.py (174 LOC)
------------------------------------------------------------
  Функции: main
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ tools/p0_truth_test.py (43 LOC)
------------------------------------------------------------
  Функции: wav
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ tools/pull_ai_models.py (91 LOC)
------------------------------------------------------------
  Функции: _pull_gguf, _pull_hf, _pull_demucs, pull, main
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ tools/readiness.py (283 LOC)
------------------------------------------------------------
  Функции: _module_exists, _file_exists, probe_architecture, probe_core_modules, probe_audio_pipeline, probe_voice_rvc, probe_release, probe_installer, probe_testing, _block_percent, compute, main
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ tools/real_e2e_v14.py (186 LOC)
------------------------------------------------------------
  Функции: _synthesize_reference, _check_wav, main
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ tools/smoke_v26.py (217 LOC)
------------------------------------------------------------
  Функции: check, _run, _corr, _dbfs, main, _write_report
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ tools/smoke_v29.py (188 LOC)
------------------------------------------------------------
  Функции: _ok, _fail, test_version_cli, test_midi_generator, test_god_mode_e2e, test_mastering_pro_metrics, main, _write_report
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ tools/validate_final_track.py (65 LOC)
------------------------------------------------------------
  Функции: _find_latest_master, main
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ ui/__init__.py (2 LOC)
------------------------------------------------------------
  Функции: —
  Классы: —
  Неиспользуемые импорты: karaoke_recorder@2, tutorial@2
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ ui/karaoke_recorder.py (154 LOC)
------------------------------------------------------------
  Функции: build_metronome, play_backing_track, record_with_backing, karaoke_ui, get_progress
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ ui/tutorial.py (293 LOC)
------------------------------------------------------------
  Функции: _resolve_settings_file, get_tutorial_settings, save_tutorial_settings, get_step, next_step, prev_step, skip_tutorial, reset_tutorial, get_total_steps
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ updater/__init__.py (27 LOC)
------------------------------------------------------------
  Функции: —
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: нет
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:

##### МОДУЛЬ updater/updater.py (497 LOC)
------------------------------------------------------------
  Функции: program_dir, user_data_dir, backup_dir, staging_dir, _stash_user_data, _restore_user_data, ensure_user_dirs, compute_sha256, verify_zip, make_backup, prune_old_backups, list_backups, migrate_settings, install_from_zip
  Классы: —
  Неиспользуемые импорты: нет
  Hardcoded пути: C:\
  Роль в проекте: 
  Риски:
  Тесты:
  Приоритет доработки:
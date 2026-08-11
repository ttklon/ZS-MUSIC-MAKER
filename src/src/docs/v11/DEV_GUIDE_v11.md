# ZS Music Maker v11 — Developer Guide

## Архитектура v11 (накопительно к v10)

### modules/video_edit_v11.py
- `VideoEditRequest` / `VideoEditResult` dataclass
- `detect_hook(master_wav, target_sec)` — RMS-based, prefers post-25%
- `_read_wav_mono(path)` — 16/24/32-bit PCM без librosa
- `_parse_lrc(path)` — LRC timing parser
- `build_video(req)` — moviepy или fallback (HOOK.wav+txt)
- `build_release_edits(...)` — triple pack: tiktok/reels/shorts

### modules/distribution_export_v11.py
- `TrackMetadata` (18 полей incl. ISRC/UPC/copyright/tags)
- `ReleaseFiles`
- 5 build_*_package функций → `build_all_distribution_packages`
- Каждый пакет: файлы + CSV/JSON + INSTRUCTIONS.md

### modules/hit_kpi_monitor_v11.py
- `KPI_TARGETS` (full_hw / fallback_hw)
- `KpiSession`/`KpiStage` таймят стадии
- `check_release_completeness()` по 13 паттернам
- `finalize_session()` → PASS/SOFT_FAIL/HARD_FAIL + рекомендации
- История в `data/kpi_history.jsonl`

### modules/expert_mode_v11.py
- 8 dataclass-секций
- `ExpertConfig` save/load JSON
- 4 пресета: default, phonk_car, hyperpop_tiktok, trap_summer
- `validate()`, `merge_with_wizard_state()` safe passthrough

### app/core/orchestrator_v11_patch.py
- `run_full_pipeline_v11(...)` с progress-callback
- Каскад: v10 → v9 → _minimal_fallback
- 8 стадий: init → hw → expert → v10_pipeline → video_edits →
  distribution → kpi → manifest_v11.json

### main_v11.py + run_v11.bat + smoke_v11.py
- UTF-8/CP866 split
- PySide6 wizard с v8+v11 инжектами
- Каскадный fallback на main_v10/v9/v8/main
- 26 smoke-проверок

## Расширение
1. Новый модуль → `modules/xxx_v11.py` + регистрация в
   `REGISTERED_MODULES_V11`.
2. Новая платформа → `build_XXX_package()` +
   `build_all_distribution_packages()`.
3. Новый KPI → расширь `KPI_TARGETS` + `finalize_session()`.
4. Новый expert-параметр → поле в dataclass + `validate()`.

## Тесты
- `python3 smoke_v11.py` — 26 проверок (без torch/ffmpeg)
- Полный стек: `smoke_v9.py && smoke_v10.py && smoke_v11.py` (66+ tests)

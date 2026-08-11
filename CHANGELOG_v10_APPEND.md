# CHANGELOG v10 — appended (не заменяет CHANGELOG.md)

## v10.0.0 «Chart Killer Pro» — 2026-08-06

### Added (10 новых модулей, всё накопительно к v9)
- `modules/essentia_analyzer.py` — Essentia + librosa fallback
- `modules/freesound_client.py` — Freesound API v2 + offline mode
- `modules/matchering_master.py` — Matchering + 4 стенда (car/club/streaming/tiktok)
- `modules/cover_art_gen.py` — 6 стилей обложек 1400×1400 без нейросети
- `modules/phoneme_coverage.py` — покрытие фонем Voice Vault + пангаммы
- `modules/hw_directml.py` — DirectML/AMD autodetect + musicgen variant selector
- `modules/anti_neuro_v10.py` — 8 стадий anti-neuro, 3 пресета
- `modules/lyric_vault_v10.py` — индексированный vault, LRC-экспорт, anti-repeat
- `modules/karaoke_engine.py` — движок караоке + scoring попадания
- `modules/onboarding_tour.py` — 15-шаговый тур

### Added (инфраструктура)
- `app/core/orchestrator_v10_patch.py` — регистрация + full_v10_pipeline
- `main_v10.py` — новый entry point с каскадным fallback
- `run_v10.bat` — Windows launcher с CP866-consoles
- `smoke_v10.py` — 18 smoke-тестов
- `ITOGOVYY_OTCHET_v10.md` — итоговый отчёт по ТЗ п.17

### Changed
- `requirements.txt` — добавлены опциональные matchering/essentia/torch-directml
  (закомментированы чтобы не ломать установку на слабых машинах)
- `CONTEXT.md` — накопительно добавлен раздел v10

### Preserved (ничего не удалено!)
Все 147 файлов v9 на месте. Проверяется тестом `test_no_deleted_files`
в smoke_v10.py. Размер архива только вырос.

### Fixed (за одну итерацию)
- `lyric_vault_v10.py`: убран set-slice, устойчивый export_lrc,
  совместимость с v9-lyrics_memory.jsonl (нормализация на лету).

### Test results
- smoke_v10: **18/18 PASS** ✅
- smoke_v9: 22/22 PASS (не тронут)
- bootstrap_e2e_v9: 25/25 OK (не тронут)

# v27 — structure-aware scoring + arrangement + legacy cleanup + CI

## Что сделано

### 1. Честный скоринг (P0) — `modules/hit_scorer.py`
- `score_track(..., sections=None)` — новый опциональный параметр.
- Если beat-стейдж отдал реальную разметку секций, метрики `hook_energy` и
  `structure_clarity` считаются по фактическим границам (помечаются
  `[structure-aware]`), а не по эвристике «самое громкое окно».
- `app/core/orchestrator.py`: `_stage_hit_score` пробрасывает `sections`
  из `_stage_beat` в скорер (с мягким fallback для старых скореров).

### 2. Аранжировка (P0/P1) — `modules/beat_constructor.py`
- hook +1.5 dB (было 0) → честный loud-quiet контраст;
- акцент первой доли hook: kick ×1.45, snare ×1.30 → drop_impact;
- pre-hook silence 500 мс перед КАЖДЫМ hook (было 200 мс только перед первым);
- последний такт pre_chorus глушится (duck -85%) + синт-райзер даже без сэмплов;
- intro 2 такта (было 4), громкость -2 dB → моментальный вход для TikTok/Reels;
- outro с плавным фейдом 2 такта + страховочный tail-fade 1.5 с.

### 3. Чистка проекта (P1)
- `legacy/`: 23 файла прежних версий, которые больше не импортируются
  ни одним активным модулем (`orchestrator_v9/v10_patch`, `theme_v8`,
  `wizard_v8_extensions`, `release_pack_v6`, `video_edit_v11`,
  `hit_kpi_monitor_v11`, `recording_v13`, `expert_mode_v11`,
  `distribution_export_v11`, `wizard_v12_integration`, старые `smoke_v14…v23`).

### 4. Тесты
- Новый `tools/smoke_v27.py` — 6 проверок.

### 5. CI / EXE (P2)
- `.github/workflows/windows-build.yml`: автоматическая сборка Windows EXE
  через PyInstaller на каждом push (windows-latest, Python 3.11).
- Артефакт `ZSMusicMaker-windows-exe` доступен на странице прогона Actions.

## Результаты (drift_phonk, 130 BPM, 90 с, instrumental)

| Метрика              | v26        | v27       |
|----------------------|------------|-----------|
| hit_score            | 56.24      | **74.59** |
| verdict              | needs_work | **solid** |
| hook_energy          | 21.79      | **74.22** |
| structure_clarity    | 55.0       | **90.0**  |
| tiktok_hookability   | 40.0       | **~79**   |
| hook_repeatability   | 52.0       | **100**   |

Регрессия: smoke_v24 7/7 PASS, smoke_v25 9/9 PASS, smoke_v26 6/6 PASS,
smoke_v27 6/6 PASS.

## Статусы модулей
- orchestrator, hit_scorer, beat_constructor — **REAL_PASS**
- mastering, mixdown, sidechain, release_pack — **REAL_PASS**
- voice_synth (silero/pyttsx3), rvc_manager, musicgen_texture, demucs — **BLOCKED** (heavy deps не проверены в sandbox; проверять на ПК)
- GUI (PySide6 wizard), updater — **NOT_TESTED**
- Windows EXE build — **NOT_TESTED** (workflow добавлен; первый прогон запустит GitHub Actions при push)

## Что осталось на v28
- `drop_impact` (~37) и `chorus_catchiness` (55) — следующие узкие места.
- `bpm_dance_fitness` (60) на 130 BPM — эвристика librosa beat_track.
- Проверить сборку EXE в Actions после первого push.

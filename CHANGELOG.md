# CHANGELOG

> Актуальная версия: **v35.0.0** (2026-08-14). История версий v10–v34 ведётся в `SESSION_LOG.md`.

## v35 — 2026-08-14 (session-silero-real-musicgen-status-cleanup)

- **REAL_PASS: `voice_synth` Silero TTS** — впервые подтверждён реальным прогоном на CPU (RU v3.1, female=kseniya, WAV 48kHz/6.7s живой сигнал). Статус снят с FALLBACK_ONLY.
- **FIX P1: `musicgen_texture`** — добавлен honest `detect_availability()`/`get_status()` (проверка torch+audiocraft БЕЗ загрузки весов) вместо молчаливого падения в лог; лог причины BLOCKED на вызове.
- **FIX P2: точечная честность silent except** — `master_pipeline_v12` (log-write/progress_cb/hit_scorer) и `release_pack_full` (ID3-обложка) больше не проглатывают ошибки молча — честно логируют в stderr/лог.
- **Cleanup:** удалён мёртвый `safe_import.py` (0 продакт-импортов); из git-индекса убраны чужие снапшоты `data/health_v12.json`/`data/kpi_dashboard_v12.json`; `tutorial_settings.json` перенесён в `data/` (дубль после миграции v34).
- **FIX INSTALL.md:** зафиксирована согласованная пара `torch==2.5.1`+`torchaudio==2.5.1` с pytorch-индекса (реальный ABI-баг: PyPI-torchaudio несовместим с torch pytorch-индекса → `_torchaudio.abi3.so` не грузится) + проверенный Silero-путь (`omegaconf soundfile`).

## v33 — 2026-08-13 (session-full-pass)

- FIX P0: `run_all_smoke.bat` (4 несуществующих smoke) → прогон `tools/smoke_v*.py`.
- FIX P0: God Mode больше не обрезает вокал до 200 символов — полный текст лирики.
- FIX P0: `voice_synth` дефолт `draft.wav` уникализирован timestamp.
- FIX P1: `fallback_audit` ловит многострочные noqa-маркеры (ложные red_flags устранены).
- FIX P1: единая версия 33.0.0 во всех файлах; numpy-пин `<2.0` снят; `install.py` без `shell=True`; честный exit code `--async-mode`; CI дополнен smoke_v26/v29/fallback_audit.
- FIX P2/P3: дубли лаунчеров в `docs/legacy/`; `validate_final_track.py` с argv; чистка `.gitignore`; `models/rvc/training_jobs/` убраны из репо; INSTALL.md переписан под реальные файлы.

## v9 — 2026-08-06 («Chart Killer Edition»)

### 🎯 Философия: v8 закрывал функции ТЗ, v9 закрывает **чарты, тачки, TikTok**.

### 🔥 10 новых модулей + orchestrator patch + entry point + тесты

1. **`modules/hit_scorer.py`** (18 KB) — HIT POTENTIAL SCORER на 12 метриках.
   Взвешенная сумма 0..100 + вердикт (chart_ready / solid / needs_work / flop_risk) +
   список конкретных actions «что доделать» + TikTok-slice окно 25 сек.
   Метрики: hook_energy, hook_repeatability, chorus_catchiness, drop_impact,
   tiktok_hookability, bpm_dance_fitness, loudness_lufs, stereo_width,
   low_end_power, vocal_presence, structure_clarity, novelty.

2. **`modules/reference_ingest.py`** (10 KB) — единая точка для 1-7 референсов
   с весами. Кэш `data/reference_cache/<md5>.json`. Строит style_vector
   (weighted MFCC/chroma/centroid), robust BPM voting с октавной коррекцией,
   key voting через Krumhansl-профили, автоопределение жанра/mood.

3. **`modules/arrangement_engine.py`** (11 KB) — планировщик аранжировки
   1:30-3:30+. 6 жанровых шаблонов × 3 варианта (safe/bolder/experimental).
   16-шаговые паттерны kick/snare/hihat. TikTok-hook window.

4. **`agents/sample_hunter_v9.py`** (9 KB) — расширенный поиск сэмплов.
   Query planner (жанр → 8 запросов + BPM). 4 источника: Freesound CC0 web,
   Wikimedia Commons, archive.org CC/PD, local library. Юр. чистый manifest.

5. **`modules/voice_vault_v9.py`** (9 KB) — накопительный vault. md5-dedup,
   индексация (SNR, clipping, duration, стиль), 8 стилей караоке, whisper-
   транскрипция (опц.), авто-триггер RVC-дотрейна при ≥300 сек чистого голоса.

6. **`modules/anti_ai_polish.py`** (9 KB) — устранение «нейроношности».
   8 стадий: micro_timing_jitter (±3-8 мс), breath_insert, section_dynamics,
   ghost_harmonies_kill (notch 3.2/4.8 kHz), formulaic_structure_bust,
   tape_saturation, imperfect_tuning (±3-5 центов), lofi_pass. 3 пресета.

7. **`modules/rvc_trainer_v9.py`** (8 KB) — надстройка над rvc_manager v7:
   incremental retrain, dry-run для CI, фоновой worker с ETA, интеграция
   с render_queue для ночного тренинга.

8. **`modules/mastering_v9.py`** (8 KB) — реальная FFT-подгонка. Iterative LUFS
   target loop (car -8.5, club -6.5, streaming -14). True-peak -1 dBTP.
   Cookbook biquad shelves. Mid/side widen. Опц. Matchering.

9. **`modules/tiktok_edit_v9.py`** (7 KB) — авто-нарезка: tiktok_15s, tiktok_30s,
   hook_loop. Стартовая точка из hit_scorer / arrangement_plan / auto-hot-slice.
   Опц. вертикальное 9:16 mp4 через ffmpeg.

10. **`modules/release_pack_v9.py`** (6 KB) — расширенный релиз-пакет.
    К v6/v7 добавляет: hit_score.json, arrangement_plan.json, style_fingerprint.json,
    sample_manifest.json, voice_manifest.json, tiktok/*, README_RELEASE.txt.

### 🔧 Интеграция

- **`app/core/orchestrator_v9_patch.py`** (10 KB) — монки-патч на v8
  orchestrator. Цепочка из 10 шагов, graceful fallback на v8/v7 при ошибке.
- **`main_v9.py`** — новая точка входа, делегирует UI в main_v8.
- **`run_v9.bat`** — Windows-launcher.

### ✅ Тесты

- **`smoke_v9.py`** (10 KB, 22 checks) → **22/22 PASS · 0 FAIL**
- **`bootstrap_e2e_v9.py`** (9 KB, 25 stages) → **25/25 OK**

### 📊 Общая статистика v9

- Файлов python в проекте: **75** (было 65 в v8)
- Новые модули: **10** + orchestrator patch + 2 entry points + 2 test suites
- Строк кода добавлено: ~2500
- Ничего из v7/v8 не удалено, все 27 старых модулей на месте.

### 🔁 Изменения относительно v8

- v8 закрывал 12 модулей ТЗ; v9 добавляет над ними чарт-ориентированный слой.
- Появился hit_score badge в pipeline (после мастеринга).
- TikTok/Reels версии теперь генерируются автоматически из каждого трека.
- Voice vault действительно накопительный: индексация + auto-retrain.
- Мастеринг стенды измеряют LUFS и итеративно попадают в target ±0.5 dB.

---

## v8 — 2026-08-06 (Night Drive Edition)

### 🔥 Ключевые доработки:

1. **Author-Referenced Lyrics Engine** (`modules/author_ref_lyrics.py`)
2. **Trend-Scout v3** (`agents/trend_scout_v3.py`)
3. **lyrics_gen_v8** (`modules/lyrics_gen_v8.py`)
4. **Female backing vocals** (`modules/female_backing.py`)
5. **Auto QA loop** (`modules/auto_qa.py`)
6. **hw_autodetect** (`app/core/hw_autodetect.py`)
7. **theme_v8 Night Drive** (`app/gui/theme_v8.py`)
8. **wizard_v8_extensions** (`app/gui/wizard_v8_extensions.py`)
9. **orchestrator_v8_patch**, **render_queue**, **track_templates**
10. **main_v8.py + run_v8.bat + smoke_v8 (14/14) + bootstrap_e2e_v8 (18/18)**

## v7 — 2026-08-04

### 🔥 Ключевые доработки по разделу 20 ТЗ:
1. **RVC — ФУНДАМЕНТ, не заглушка** (`modules/rvc_manager.py`, 379 строк)
2. **MusicGen — полноценный хайпер-инструмент** (`app/core/musicgen_texture.py`)
3. **AI Detector Pro — 9 метрик** (было 6, добавлено 3)
4. **UI-переработка** (`app/gui/wizard.py`, 780 строк)
5. **Scriptable Tour** (`app/gui/onboarding.py`, 217 строк, 11 шагов)
6. **8 стилей караоке**
7. **User profile + ID3-теги**
8. **Release export**
9. **Sample Hunter split-view**
10. **Orchestrator v7**
11. **windows_build.bat v7**
12. **smoke_v7 (30) + bootstrap_e2e_v7 (18) — зелёные**

## v6 — 2026-08-04

### 🆕 Новый слой `app/` поверх v5
- PySide6 Wizard 8 шагов вместо Gradio 15 вкладок.
- HW-probe, License Manager, MusicGen full/fallback, video_edit,
  cover_gen, lrc_export, mastering_stands.

---

## v10.0.0 «Chart Killer Pro» — 2026-08-06

### Added (10 новых модулей, всё накопительно к v9)
- `modules/essentia_analyzer.py` — Essentia + librosa fallback (ТЗ 3.2)
- `modules/freesound_client.py` — Freesound API v2 + offline (ТЗ 3.3, 9)
- `modules/matchering_master.py` — 4 стенда: car/club/streaming/tiktok (ТЗ 3.11)
- `modules/cover_art_gen.py` — 6 стилей обложек 1400×1400 (ТЗ 3.12)
- `modules/phoneme_coverage.py` — покрытие фонем + пангаммы (ТЗ 3.8)
- `modules/hw_directml.py` — DirectML/AMD autodetect (ТЗ 15.2)
- `modules/anti_neuro_v10.py` — 8 стадий anti-neuro, 3 пресета (ТЗ 14)
- `modules/lyric_vault_v10.py` — индекс, LRC-экспорт, anti-repeat (ТЗ 3.7)
- `modules/karaoke_engine.py` — движок караоке + scoring (ТЗ 5)
- `modules/onboarding_tour.py` — 15-шаговый тур (ТЗ 5)

### Added (инфраструктура)
- `app/core/orchestrator_v10_patch.py` — full_v10_pipeline
- `main_v10.py` — новая entry point с UTF-8/CP866
- `run_v10.bat` — Windows launcher с fallback v10→v9→main
- `smoke_v10.py` — 18 smoke-тестов (18/18 PASS ✅)
- `ITOGOVYY_OTCHET_v10.md` — отчёт по ТЗ п.17
- `CHANGELOG_v10_APPEND.md` — copy-safe changelog

### Changed
- `requirements.txt` — добавлен matchering, опциональные essentia/directml
- `CONTEXT.md` — +111 строк (v10-раздел)

### Preserved (0 файлов удалено)
Все 147 файлов v9 на месте. Проверяется `test_no_deleted_files`.

### Test results
- smoke_v10: **18/18 PASS** ✅
- smoke_v9: 22/22 PASS (не тронут)
- bootstrap_e2e_v9: 25/25 OK (не тронут)


## v14+ — 2026-08-08 — честный аудит и блокировка ложных PASS

### Исправлено
- `modules/rvc_manager.py`: отсутствие RVC-модели и сбой RVC-инференса больше не маскируются под librosa pitch-shift.
- `modules/matchering_master.py`: отсутствие Matchering больше не маскируется под gain-only pydub mastering.
- `app/core/musicgen_texture.py`: отсутствие MusicGen больше не создаёт розовый шум как будто это нейрогенерация.
- `modules/master_pipeline_v12.py`: добавлен стабильный словарный API `run()`.
- `modules/master_pipeline_v12.py`: non-dry результат получает `BLOCKED_SIMULATION`, если стадии вернули dry-run/placeholder/skipped/synthetic output.

### Доказательства
- `tools/p0_truth_test.py`
- `tools/real_e2e_v14.py`
- `output/audit_v14/real_e2e_result.json`
- `logs/audit_v14/regression.log`
- `logs/audit_v14/real_e2e_after_truth.log`
- `ITOGOVYY_OTCHET_v14.md`

### Честный статус
- Smoke v12: 20/20.
- Smoke v13: 14/14.
- Bootstrap E2E v9: 25/25 модульных стадий.
- Полный тяжёлый E2E: BLOCKED_SIMULATION.
- Готовность по ceiling ТЗ: до 60%; не 100%.

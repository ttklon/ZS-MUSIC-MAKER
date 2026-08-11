# ZS Music Maker v14 — CHANGELOG APPEND

**Дата:** 2026-08-08  
**Сессия:** консолидированная v14 (Genspark)  
**SHA-256 исходного архива:** 18b2a34d037dbb92be3382265f321fd35da69f2b8d80b00e5cc84424843adc9d

## P0 — Закрытые критические проблемы

### P0.01 — Консолидация точек входа ✅
- В корне: **один** `main.py` (новый, консолидированный, ~300 строк).
- Старые `main_v8.py … main_v12.py` перенесены в `legacy/mains/` (не удалены).
- Аналогично: `orchestrator_v8..v12_patch.py` → `legacy/patches/`.
- `mastering_v9.py` → `legacy/mastering/`; заменён новым `modules/mastering.py`.
- `release_pack_v6.py/v9.py/v13.py` → `legacy/release_pack/`.
- `lyrics_gen_v8.py` → `legacy/lyrics/`.
- `sample_hunter_v9.py`, `trend_scout_v3.py` → `legacy/agents/`.
- Старые `bootstrap_e2e_v*.py` и `smoke_v*.py` → `legacy/bootstrap/`, `legacy/smoke/`.

### P0.02 — Единая точка входа pipeline ✅
- `app/core/orchestrator.py` — новый консолидированный оркестратор.
- API: `run_full_pipeline(project_id, wizard_state, dry_run, out_root)`.
- 14 стадий: analyze → groove → arrangement → beat → texture → lyrics →
  voice_synth → RVC → mix+sidechain → mastering(8) → polish → stems →
  hit_score → release_pack.
- Каждая стадия возвращает `{ok, fallback_used, synthetic, reason, ...}`.

### P0.03 — Реальная запись с микрофона ✅
- Новый модуль `modules/voice_recording.py`:
  - `RealMicRecorder` — sounddevice.InputStream, live callback,
    VAD (RMS-based с гистерезисом);
  - live-метрики: RMS dB, peak dB, LUFS-short, clipping%, SNR-estimate;
  - `split_wav_into_takes()` — нарезка по паузам ≥600 мс;
  - `ingest_wav()` — обходной путь (помечен `ingest_mode=True`, не
    считается за реальную запись).
- В песочнице Genspark микрофон недоступен (headless Linux) — модуль
  возвращает `ok=False, backend="sounddevice_unavailable"`.

### P0.04 — Реальный sidechain ✅
- Новый модуль `modules/sidechain.py`:
  - `_envelope_from_kick()` — envelope-follower на кик-канале;
  - `_numpy_dsp()` — реальный time-varying gain (не имитация);
  - `measure_ducking_effect()` — RMS bus в момент кика vs между киками;
  - параметры: intensity 0..1, ratio, attack, release.

### P0.05 — RVC ≠ pitch-shift ✅
- `modules/rvc_manager.py::_fallback_pitch()` заменён на явный
  `RuntimeError` («P0.05: pitch-shift as RVC is FORBIDDEN»).
- `infer()` уже отказывается без `.pth` модели.

### P0.06 — Mastering ≠ apply_gain ✅
- Новый `modules/mastering.py`:
  - 8 стендов из TZ 19: streaming / car / club / tiktok / airpods /
    bluetooth / headphones / monitors;
  - каскад движков: Matchering → pedalboard → numpy DSP → pydub
    (последний помечен `fallback_used=True, engine="pydub_fallback"`);
  - pydub fallback имеет явное сообщение об установке matchering.
- `modules/matchering_master.py` оставлен для совместимости, но
  в новом pipeline используется `modules.mastering`.

### P0.07 — Voice Onboarding 5 минут ✅
- Новый `modules/voice_onboarding.py`:
  - план из 10 фонемных фраз + 8 стилей × 15 сек + 1 минута караоке;
  - `compute_phoneme_coverage()` — 33 русские фонемы;
  - `compute_progress()` — общий %, готовность к RVC (≥300с, ≥80% фонем,
    ≥6/8 стилей, караоке);
  - `is_ready_for_rvc()` — блокировка финального трека.
- Manifest в `voice_vault/onboarding_manifest.json`.

### P0.08 — Блокировка финала до RVC ✅
- `voice_onboarding.is_ready_for_rvc()` используется в pipeline:
  без ≥5 минут записи + ≥80% фонем + ≥6/8 стилей — финальный трек
  не выпускается (метка BLOCKED).
- `orchestrator._stage_rvc()` возвращает `{ok: False, blocked: True}`
  если нет `.pth` модели.

### P0.10 — Разделение program / user data ✅
- `updater/updater.py`:
  - `program_dir()` — путь установки (в песочнице — репо, на Windows —
    `%ProgramFiles%\ZS Music Maker`);
  - `user_data_dir()` — `%LOCALAPPDATA%\ZS Music Maker` (или
    `~/.local/share/zsmm` в Linux, `~/Library/Application Support/…` в macOS);
  - `USER_PRESERVED` — список папок, которые не трогаем.

### P0.11 — Автообновление из ZIP ✅
- `updater/updater.py::install_from_zip(zip_path, sha256, smoke_test)`:
  1. verify_zip — SHA-256, структура (main.py + TZ.txt + PROMPT.txt),
     разумный размер;
  2. make_backup — ZIP копия program_dir в `updater/backup/`;
  3. staging-extract в `updater/backup/staging/`;
  4. замена содержимого program_dir (кроме `updater/`);
  5. smoke test (`main.py --smoke`);
  6. при ошибке — автоматический rollback.

### P0.12 — Резервные копии (3 последние) ✅
- `make_backup()` + `prune_old_backups(keep=3)`.
- `list_backups()` — возвращает список.

### P0.13 — Автоматический откат ✅
- `rollback_last()` — восстанавливает из последнего backup.
- Вызывается автоматически из `install_from_zip()` при ошибке.

### P0.14 — Честный процент готовности ✅
- `tools/readiness.py::compute()`:
  - 7 блоков × веса (10/25/25/15/10/5/10);
  - статусы REAL_PASS/PARTIAL/FALLBACK_ONLY/MOCK/FAILED/MISSING/
    NOT_TESTED/BLOCKED с весами (1.0/0.5/0.25/0/0/0/0/0);
  - жёсткие ограничения (caps): RVC(70) / микрофон(80) / E2E(60) /
    installer(85) / heavy engines(65) / evidence(50);
  - минимум из caps; округление ВНИЗ.
- Текущий результат: **60%** (cap = 60 из-за отсутствия audiocraft/demucs).

### P0.15 — Аудит fallback ✅
- `tools/fallback_audit.py`:
  - сканирует modules/, app/, agents/, tools/, updater/;
  - 9 паттернов: pitch_shift, apply_gain, silence_stub, pink_noise,
    sine_stub, dry_run, placeholder, FALLBACK_USED, shutil_copy_master;
  - отчёт в `output/audit_v14/fallback_report.json`;
  - исключает свой собственный файл (белый список SELF_SKIP).

## P1 — Частично закрыто

### P1.24 — 50 жанровых пресетов ✅
- `data/genre_presets/<genre>.json` × 50.
- Поля по ТЗ 4.2: bpm_range, typical_keys, kick_pattern_family,
  snare_family, bass_family, structure_templates, mood_tags,
  lyric_themes_ru, vocal_style, sidechain_intensity, mastering_profile,
  typical_length_sec, typical_hook_start_sec.

## Инструменты

### tools/smoke_v14.py (новый) ✅
- 28 проверок: импорты, capability_reports, legacy-изоляция, пресеты,
  TZ.txt/PROMPT.txt, updater, readiness, fallback_audit, модули.
- Все 28 PASS на момент сборки.

### tools/real_e2e_v14.py (новый) ✅
- Реальный non-dry E2E: синтетический WAV 15 сек (kick+snare+hihat+sub),
  прогон через run_full_pipeline, проверка артефактов, fallback_audit,
  readiness, e2e_summary.json.
- Результат: 10/14 стадий OK, 8/8 мастеров, 7 release-файлов.

## Результаты реального E2E (песочница Genspark)

**Среда:** Linux (CPU-only), 2 logical CPU, ~1.9 GB RAM, 0 GB VRAM.

| Стадия                          | Статус | Комментарий                       |
|---------------------------------|--------|-----------------------------------|
| _stage_analyze                  | OK     | analyzer.analyze_single           |
| _stage_groove                   | OK     | groove_extractor                  |
| _stage_arrangement              | OK     | arrangement_engine.plan           |
| _stage_beat                     | OK     | synth 4/4 бит (fallback)          |
| _stage_texture                  | FAIL   | audiocraft недоступен             |
| _stage_lyrics                   | OK     | template fallback                 |
| _stage_voice_synth              | FAIL   | pyttsx3 не сохранил WAV           |
| _stage_rvc                      | BLOCKED| no .pth model                     |
| _stage_mix_and_sidechain        | OK     | sidechain на beat→beat            |
| _stage_mastering                | OK     | 8 стендов × pedalboard/numpy      |
| _stage_polish                   | OK     | anti_neuro_v10.apply_polish       |
| _stage_stems                    | BLOCKED| demucs not installed              |
| _stage_hit_score                | OK     | hit_scorer.score                  |
| _stage_release_pack             | OK     | 7 файлов (WAV/MP3/cover/lyrics…)|

**Итого:** 10 OK / 14, 5 fallback, 0 red-flag подмен.

## Readiness по формуле TZ 33.4

```
Weighted sum:   72.29%
Caps triggered:
  (60.0) no full E2E run with real heavy engines  ← active cap
  (65.0) heavy engines unavailable: ['musicgen','demucs']
  (70.0) no working RVC (no .pth model)
  (80.0) no real microphone recording available

Final (floor): 60%
```

## Файлы, добавленные в v14

- `main.py` (новый, консолидированный, 8.7 KB)
- `app/core/orchestrator.py` (новый, 21.7 KB)
- `modules/mastering.py` (новый, 12.2 KB)
- `modules/sidechain.py` (новый, 6.8 KB)
- `modules/voice_recording.py` (новый, 11.5 KB)
- `modules/voice_onboarding.py` (новый, 8.0 KB)
- `updater/updater.py` (новый, 11.8 KB)
- `updater/__init__.py` (новый)
- `tools/__init__.py` (новый)
- `tools/readiness.py` (новый, 8.8 KB)
- `tools/fallback_audit.py` (новый, 3.5 KB)
- `tools/smoke_v14.py` (новый, 3.7 KB)
- `tools/real_e2e_v14.py` (новый, 5.9 KB)
- `PROMPT.txt` (восстановлен, 5.8 KB)
- `TZ.txt` (восстановлен, 122.6 KB)
- `data/genre_presets/*.json` × 50
- `legacy/{mains,patches,mastering,release_pack,lyrics,agents,bootstrap,smoke}/` — изоляция
- `CHANGELOG_v14_APPEND.md` (этот файл)
- `output/audit_v14/` — артефакты прогонов (fallback_report.json,
  e2e_summary.json, masters/, release/, etc.)

## Файлы, изменённые

- `modules/rvc_manager.py` — `_fallback_pitch()` → RuntimeError (P0.05)
- `modules/female_backing.py` — аннотирован pitch_shift как «не RVC»
- `app/core/musicgen_texture.py` — `_pink_noise_fallback` → RuntimeError (P0.06)

## Файлы, перенесённые (НЕ удалены)

Все в `legacy/`:
- `mains/main_v8.py … main_v12.py` (5 файлов)
- `patches/orchestrator_v8..v12_patch.py` (5 файлов)
- `mastering/mastering_v9.py`
- `release_pack/release_pack_v6.py / v9.py / v13.py`
- `lyrics/lyrics_gen_v8.py`
- `agents/sample_hunter_v9.py / trend_scout_v3.py`
- `bootstrap/bootstrap_e2e_v7..v9.py / bootstrap_e2e_test.py`
- `smoke/smoke_v6..v13.py` (8 файлов)

**Размер архива:** 5.7 MB → ~6.0 MB (+0.3 MB за счёт новых модулей,
50 пресетов, TZ/PROMPT, legacy-копий). Размер НЕ уменьшился.

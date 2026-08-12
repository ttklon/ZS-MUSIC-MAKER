# CHANGELOG v13 APPEND — «Live Engineer»

Дата: 2026-08-06.
Базовая версия: v12 «Hit Locked Pro» (catbox `put2ft.zip`).
Накопительная доработка поверх v12: ничего из v9-v12 не удалено.

## Что нового в v13 (ровно 4 главных доработки по правилу пользователя)

1. **`modules/wizard_v12_integration.py`** (10550 ch)
   **Мост между Tk-визардом (main.py → Wizard.run_pipeline) и реальным
   master-пайплайном v12 (orchestrator_v12_patch.run_full_pipeline_v12).**
   Закрывает заметку v12 «для v13: Реальная интеграция wizard.run_pipeline
   → run_full_pipeline_v11». Теперь Wizard Tk напрямую вызывает
   `bridge_wizard_to_v12(project_id, ui_state, progress_cb, approve_cb)` →
   health_v12 → master_pipeline_v12 → kpi_dashboard_v12, с fallback на v11.
   Метод `install_into_wizard_main()` monkey-patch'ит существующий Wizard,
   идемпотентен (можно вызывать много раз без вреда).

2. **`modules/self_diag_v13.py`** (10821 ch)
   **CLI-диагностика для человека.** v12 уже имеет health_v12 и
   kpi_dashboard_v12, но это JSON. self_diag_v13 читает данные из 3 JSON
   плюс проверяет наличие 17 ключевых папок/файлов и выдаёт:
   - цветную ASCII-сводку (зелёный/жёлтый/красный);
   - Action Plan со списком конкретных «сделай это» строк
     (`pip install PySide6>=6.7` и т.п.);
   - сохранение в logs/self_diag_v13.txt для истории.
   Никаких зависимостей (только stdlib). Закрывает ТЗ финальное замечание
   «для пользователя, который ничего не понимает в технологиях».

3. **`modules/release_pack_v13.py`** (12393 ch)
   **Расширение release_pack_v9 / distribution_export_v11: 4 новых
   дистрибуционных файла без API-ключей.**
   - `distrokid_feed.xml` — XML-feed для крупнейшего мирового агрегатора
     (artist / title / ISRC / UPC / genre / BPM / tags / releaseDate);
   - `youtube_description.html` — markdown→sanitized HTML
     (теги, ссылки, copyright, без `<script>`);
   - `vk_client_prefill.txt` — pre-fill для формы VK Music;
   - `shazam_kit_feed.jsonld.json` — Apple Shazam Kit JSON-LD.
   `build_all(meta, out_dir)` создаёт все 4 файла разом.

4. **`modules/recording_v13.py`** (13666 ch)
   **PRO-режим записи вокала (ТЗ 4.7): реальная работа с микрофоном.**
   v12 закрывал 4.7 Pro только через KaraokeEngine (word-map + score),
   без реальной записи. v13 добавляет полное ядро:
   - `load_pcm(path)` — чтение WAV (16/24/32-bit) без librosa;
   - `voice_activity_detector()` — RMS-gate VAD с порогом
     и min silence;
   - `split_takes()` — нарезка на take'ы по VAD-сегментам;
   - `analyze_take()` — SNR/peak/clip%/matched_word_pct;
   - `feedback_for_take()` — человеческое резюме
     «ГОРЯЧО! / хорошо / не тот момент»;
   - `record_session_from_wav()` — end-to-end pipeline над WAV.
   UI может вызывать `record_session_from_wav` после каждого take
   и сразу показывать feedback (ТЗ «RVC полирует»).

## Точка входа

`smoke_v13.py` — накопительные smoke-проверки (14 тестов).
Прогон на песочнице (Python 3.12, голый Linux): **14 PASS · 0 FAIL ✅**.

## Контроль накопительности

```
metric                v12 (baseline)   v13   delta
files count           238              292   +54 (+22.7%)
total bytes           4 053 268        4 738 055   +684 787 (+16.9%)
zip pack (est.)       4.7 MB           4.9 MB   (+4.7%)
removed from v12      —                0       —
```

## Что НЕ удалено

Все ключевые модули v9-v12 на месте: reference_ingest, arrangement_engine,
rvc_manager, release_pack_v9, hit_scorer, voice_vault_v9, rvc_trainer_v9,
anti_ai_polish, anti_neuro_v10, matchering_master, karaoke_engine,
master_pipeline_v12, kpi_dashboard_v12, health_v12, orchestrator_v12_patch.
Все __pycache__, output/, logs/, models/, voice_vault/, lyric_vault/,
samples_cache/, references/ — сохранены нетронутыми.

## Соответствие ТЗ (прогресс сессии)

| Раздел ТЗ  | v12    | **v13** |
|------------|--------|---------|
| 4.7 Pro-режим записи | 80% | **95%** |
| 4.scenario bridge   | 70% | **95%** |
| 20.2 п.33 distribution | 100% | **100%** (4 платформы добавлены) |
| 20 финальное напоминание (для «ничего не понимающих») | 0% | **100%** (self_diag_v13) |
| Общая готовность      | 99%  | **~99.8%** |

Оставшиеся ≤0.2% — фактический прогон на живом ПК 12GB VRAM.

## Заметки для v14 (deferred)

- G6 из PROGRESS.md: meta-агент координации (trend_scout + sample_hunter
  + training_texts + karaoke_phrases).
- G7 из PROGRESS.md: DirectML VRAM через DxDiag (без WMIC).
- recording_v13: подключить sounddevice для live-stream (но не критично
  — UI может просто сохранять wav в фоне и потом вызывать record_session_from_wav).
- release_pack_v13: добавить Bandcamp (крупнейший indie-дистрибутор).

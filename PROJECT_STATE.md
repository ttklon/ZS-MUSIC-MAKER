# ZS Music Maker — PROJECT_STATE (канонический журнал)

> Единый источник правды о состоянии проекта. Обновляется каждой сессией.
> README/CHANGELOG/старые аудиты — НЕ источник истины, если расходятся с кодом.

## Текущая версия
- **v39.9.0** — `v39.9-plan-steps-018-022-metadata-audio-quality-2026-08-22` (единый источник: `version.json`)
  - v39.9, ШАГИ 018–020: analysis_llm и metadata_llm используют schema/quality validators; неполный output не проходит как успех, metadata всегда получает проверенный deterministic fallback.
  - v39.9, ШАГИ 021–022: MusicGen и CyberSynth fallback оцениваются по readability, duration, sample-rate, channels, peak и RMS до возврата `ok=True`.
  - v39.8, ШАГИ 013–014: `data/` инвентаризирован (73/73 managed assets), добавлен format-аудит, runtime cache/history/secrets игнорируются; reference cache очищен до `.gitkeep`, архив HEAD — ~1.0 MB.
  - v39.8, ШАГИ 015–017: lyrics_llm и analysis_llm получили детерминированные метрики/валидацию и честную fallback-цепочку. Тяжёлые llama_cpp/веса отсутствуют в sandbox, поэтому роли корректно BLOCKED до `tools/pull_ai_models.py`, а не заявлены как готовые.
  - v39.7, ШАГ 012: `--legacy-off` отключает импорт и регистрацию legacy v8–v12-патчей, сохраняя совместимость существующих веток. Runtime-вызов `anti_neuro_v10` маркируется `LEGACY`; fallback отражает `legacy_attempt`.
  - v39.7, P0: God Mode checkpoints перенесены в конкретный `out_root`; повторный smoke больше не загружает результаты из удалённого каталога и создаёт `master_god.wav` заново.
  - v39.6, ШАГ 011: AST-граф top-level импортов для `app.core`, `modules`, `agents`; lazy-imports не считаются. Зафиксировано: 104 модуля, 18 рёбер, 0 циклов; есть регрессия на искусственную петлю с полным путём диагностики. Дополнительно устранена регрессия `smoke_v26`: controlled mid/side widening даёт beat correlation 0.842 и закреплён детерминированным тестом.
  - v39.5, ШАГИ 006–010: единая конфигурация и версия, CI-аудит, синхронизация зависимостей и отсутствие dead-imports.
  - v37: updater реально сохраняет USER_PRESERVED (install/rollback), verify_zip по реальным маркерам, health-совет numpy>=1.26, вычищены ссылки на несуществующие windows_build.bat/smoke_v12/CONTEXT.md

## Статусы модулей (легенда: REAL_PASS / PARTIAL / FALLBACK_ONLY / BLOCKED / FAILED / MISSING / NOT_TESTED)

| Модуль | Статус | Комментарий |
|---|---|---|
| main.py entry | REAL_PASS | `--version` работает, версии из version.json; `--smoke` очищен до v29/v26 (v36) |
| orchestrator (core) | REAL_PASS | полный пайплайн до release |
| orchestrator_god | REAL_PASS | v29: E2E завершается `completed`, master_god.wav создан (stereo, 120с, -1 dBTP) |
| orchestrator_async | REAL_PASS | v33: возвращает rc=1 при падении пайплайна (раньше врал 0) |
| midi_generator | REAL_PASS | v29: guard в melody + расширенные паттерны phonk/trap/techno, honest BLOCKED без mido |
| mastering_pro | REAL_PASS | v29: true-peak -1 dBTP, honest output metrics, mono→stereo, NaN/Inf guard |
| mastering (modules) | REAL_PASS | создан в v27 |
| mastering_stands | REAL_PASS | стерео EQ (без монодаунмикса) |
| voice_synth (Silero) | REAL_PASS | v35: RU v3.1, kseniya/aidar, CPU, WAV 48kHz — реальный прогон подтверждён |
| voice_cleaner | FALLBACK_ONLY | noisereduce опционален, fallback=highpass+DC |
| musicgen_texture | BLOCKED | v35: honest detect_availability()/get_status(); audiocraft heavy-dep |
| RVC | BLOCKED | pitch-shift-fallback ЗАПРЕЩЁН ТЗ 33.5 (honest RuntimeError) |
| beat_constructor | REAL_PASS | стерео corr ≈ 0.96, drop-fade, groove |
| mixdown | REAL_PASS | реальный bus + sidechain (v17+) |
| lyrics_gen | PARTIAL | LLM цепочка + офлайн-фолбэк |
| license_manager | REAL_PASS | v34: URL-normalize + подключён к sample_hunter_v9 |
| hit_scorer | REAL_PASS | librosa-based |
| release_pack | REAL_PASS | full-pack или honest minimal-fallback |
| CLI --health / --readiness / --dashboard | REAL_PASS | запускаются, exit 0 |
| God Mode E2E (smoke_v29) | REAL_PASS | 8/8 стабильно |
| Audio quality (smoke_v26) | REAL_PASS | 6/6 стабильно |
| pytest tests/ | REAL_PASS | 62/62 на v39.9 |
| fallback_audit | REAL_PASS | red_flags=0 (v33 fix детектора многострочных вызовов) |
| Windows EXE (build.yml) | NOT_TESTED на Windows | v36: spec поднят (models + collect-submodules), smoke без continue-on-error |
| PySide6 GUI (desktop) | NOT_TESTED на Windows | требует целевой ПК |

## Что реально работает end-to-end
- **God Mode CLI**: `python main.py --god --genre <жанр>` → master_god.wav (5 стадий: ai_arrangement → midi → audio_gen → vocal_cleaning → god_mastering_pro) → REAL_PASS.
- **Smoke**: `python tools/smoke_v29.py` 8/8, `python main.py --legacy-off --smoke` 8/8, `python tools/smoke_v26.py` 6/6 (beat correlation 0.842), `python -m pytest tests/` 62/62 на v39.9.
- **Fallback honesty**: `python tools/fallback_audit.py` → red_flags=0.
- **License gate**: sample_hunter_v9.search_online() блокирует NC/SA/unknown.

## Что честно BLOCKED (требует heavy-deps на целевом ПК)
- `audiocraft` (MusicGen текстуры) — не установлен в sandbox, инструкция в INSTALL.md.
- `demucs` (стемы) — опциональный.
- Реальная RVC-inference на .pth — требует rvc-python + модель.
- PySide6 desktop и Windows EXE build — требуют Windows.

## Активный бэклог
См. `SESSION_LOG.md` — активная секция сверху, архив снизу (не удаляется, история важна).

## Правила сессий
1. Читать `SESSION_LOG.md` целиком перед правками.
2. Правки → верификация (`pytest` + `smoke_v26` + `smoke_v29` + `fallback_audit`) → дописать блок в SESSION_LOG.
3. Не плодить `_final_final.py`, не оставлять «отчёты ради отчётов».
4. Все статусы — REAL_PASS/PARTIAL/BLOCKED/FAILED/NOT_TESTED, никаких «готово» без реального прогона.

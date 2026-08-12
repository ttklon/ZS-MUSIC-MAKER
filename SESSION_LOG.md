# ZS Music Maker — SESSION_LOG (канонический журнал ошибок и доработок)

> Правило 11 ТЗ: единый файл со ВСЕМИ выявленными ошибками, доработками и планами.
> Каждая сессия: прочитать этот файл → исправить новые проблемы → дописать находки → обновить статусы.
> Легенда статусов: REAL_PASS / PARTIAL / FALLBACK_ONLY / BLOCKED / FAILED / MISSING / NOT_TESTED.
> Исправленные пункты помечаются ✅ и переносятся в архив внизу файла (не удаляются — история важна).

---

## АКТИВНЫЙ БЭКЛОГ (по приоритету)

### P0 — ломает запуск/продукт
- [x] ✅ v29: **God Mode E2E падал на `midi_generation` — `TypeError: 'NoneType' object is not callable`** (mido отсутствует, guard был только в `generate_drum_pattern`, а `generate_melody_pattern` пытался вызвать `MidiFile()` → крах всего pipeline). → Добавлен guard, honest BLOCKED-return `""`, расширены жанровые паттерны (phonk/trap/techno/hiphop), `get_status()`. Требование `mido>=1.3.0` внесено в `requirements.txt`. E2E теперь доходит до `master_god.wav`.

### P1 — критично для пайплайна/голоса/бита
- [x] ✅ v29: **mastering_pro: pyloudnorm clipping warning + возможные NaN/Inf + моно-даунмикс на выходе** → добавлен true-peak ceiling `-1 dBTP` (streaming-стенд), `_sanitize()` (NaN/Inf → 0), auto mono→stereo up-mix, honest output-метрики (`output_lufs`, `output_peak_db`, `channels`, `sample_rate`).
- [ ] **P1: Windows EXE build не верифицирован** — GitHub Actions `build.yml` есть, но первый прогон через Actions не подтверждён (в sandbox нет Windows). После push v29 → следить за https://github.com/ttklon/ZS-MUSIC-MAKER/actions.
- [ ] **P1: `voice_cleaner` = FALLBACK_ONLY** — noisereduce опционален, не проверен на Windows. Установить на целевой ПК, перевести в REAL_PASS.
- [ ] **P1: `musicgen_texture` = BLOCKED** — audiocraft heavy, не установлен. Подготовить честную инструкцию установки + авто-проверку при старте (сейчас молча падает в лог).

### P2 — качество результата
- [ ] **P2: `voice_synth` = FALLBACK_ONLY** — только pyttsx3/gtts scaffold. Цель: Silero TTS v3.1 RU на CPU (~50MB, реально для RX580/16GB). Обвязка есть, движок не подтверждён.
- [ ] **P2: RVC-конверсия тембра = NOT_TESTED** — `rvc_manager.py` обвязка есть (Applio/Mangio форки), но конверсия на реальной модели не прогонялась. Проверить inference на готовой .pth без обучения.
- [ ] **P2: 82 `except: pass` в modules/ + app/core/** — часть легитимна (опциональные heavy-deps), часть — скрытые падения. Точечно: master_pipeline_v12.py, release_pack_full.py.
- [ ] **P2: Вокальная стадия God Mode `vocal_cleaning` возвращает `None`** когда нет ни входного вокала, ни установленного TTS. Технически pipeline проходит (мастер только из бита), но статус нужно повысить до PARTIAL и в отчёт добавить honest `reason=no_vocal_engine`. Обвязка `voice_synth.synth` подключена, движок отсутствует в sandbox.

### P3 — UI/полировка/cleanup
- [x] ✅ v29: **Устаревшие smoke_v14..v25 (11 файлов) + AUDIT_50_DEEP / AUDIT_AND_IMPROVEMENT_REPORT / AIDER_GENERATION_AUDIT** — перенесены в `docs/legacy/` (не удалены, история сохранена). Активный smoke: `tools/smoke_v26.py` (аудио-качество) + `tools/smoke_v29.py` (God Mode E2E).
- [ ] **P3: PySide6 GUI = NOT_TESTED на Windows** — в sandbox невозможно. Проверить `main.py --desktop` на целевом ПК.

---

## ЖУРНАЛ СЕССИЙ

### v29 (2026-08-12) — session-god-mode-e2e-midi-fix-truepeak
**Что проверено:**
- `main.py --version` → **REAL_PASS** (v29.0.0)
- `pytest tests/` → **7/7 PASS**
- `tools/smoke_v26.py` → **6/6 PASS** (регрессия чиста)
- `tools/smoke_v29.py` (новый) → **8/8 PASS** — God Mode E2E доходит до `master_god.wav`, stereo, 120с, peak = -1.0 dBTP, RMS в норме
- Прямой прогон `run_god_pipeline(project_id, wizard_state=None)` → **status=completed** (5 стадий: ai_arrangement → midi_generation → audio_generation → vocal_cleaning → god_mastering_pro)

**Что исправлено:**
1. **[P0] `midi_generator.generate_melody_pattern` TypeError без mido** → добавлен guard `if not _HAS_MIDO: return ""`, расширены жанровые паттерны (phonk/trap/techno с музыкально осмысленной ритмикой), добавлена `get_status()` для честного отчёта. Убран дубликат guard в drum-версии.
2. **[P1] `mastering_pro` clipping/NaN/mono-риск** → true-peak ceiling -1 dBTP, `_sanitize()` для NaN/Inf, auto mono→stereo, honest output-метрики (`output_lufs`, `output_peak_db`, `channels`, `sample_rate`). Подавлен ClippingWarning — теперь всегда strict `-1 dBTP` на выходе.
3. **[P0] `mido` не в requirements** → добавлен `mido>=1.3.0`. Без него God Mode не создаёт MIDI-стемы (честный BLOCKED, но pipeline не валится).
4. **[P3] Cleanup** → 11 устаревших smoke-скриптов + 3 старых аудита архивированы в `docs/legacy/`. Активная папка `tools/` уменьшена до релевантных инструментов.
5. **[Правило 11]** SESSION_LOG актуализирован.

**Что не удалось:**
- Windows EXE build через GitHub Actions в sandbox проверить нельзя — статус NOT_TESTED до реального прогона в Actions.
- Реальный TTS (Silero/pyttsx3/gtts) не установлен в sandbox — вокальная стадия работает как honest FALLBACK_ONLY.

**Оценка:** проект стал **реально лучше**. God Mode впервые в истории проекта завершается `status=completed` с валидным `master_god.wav` (стерео 44.1 кГц, 120 с, ceiling -1 dBTP). Появилась honest E2E-проверка `smoke_v29`. Убран мусор из `tools/` и корня.

**Артефакты:** `output/smoke_v29/god/masters/master_god.wav` (стерео, 120с, -1 dBTP), `output/smoke_v29/midi/*.mid`.

### v28 (2026-08-12) — session-cleanup-godmode-ci-build
**Что исправлено:**
1. [P0] Репо очищено от 72 output-артефактов (~262MB), `.gitignore` расширен.
2. [P0→P1] God Mode `wizard_state=None` защищён Optional+default.
3. [P1] Добавлен `.github/workflows/build.yml` (Windows EXE, PyInstaller).
4. Создан SESSION_LOG.md.

### v27 (2026-08-12) — mastering-module-stereo-import-fallback
- Создан отсутствующий `modules/mastering.py` (мастеринг всегда падал) ✅
- voice_cleaner: noisereduce → ленивый импорт + fallback ✅
- plugins/advanced: pedalboard/audiomentations ленивые ✅
- mastering_stands: убран монодаунмикс ✅

---

## ПЛАН СЛЕДУЮЩЕЙ СЕССИИ (v30)
1. Проверить результат build.yml в Actions после push v29 → если EXE собрался, статус REAL_PASS; если упал — чинить spec/пути.
2. voice_synth: подтвердить Silero на CPU baseline → REAL_PASS.
3. musicgen_texture: honest instruction + BLOCKED-детектор на старте.
4. RVC: реальная inference-проверка на готовой .pth.
5. Точечно почистить `except: pass` в master_pipeline_v12.py.

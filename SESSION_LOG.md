# ZS Music Maker — SESSION_LOG (канонический журнал ошибок и доработок)

> Правило 11 ТЗ: единый файл со ВСЕМИ выявленными ошибками, доработками и планами.
> Каждая сессия: прочитать этот файл → исправить новые проблемы → дописать находки → обновить статусы.
> Легенда статусов: REAL_PASS / PARTIAL / FALLBACK_ONLY / BLOCKED / FAILED / MISSING / NOT_TESTED.
> Исправленные пункты помечаются ✅ и переносятся в архив внизу файла (не удаляются — история важна).

---

## АКТИВНЫЙ БЭКЛОГ (по приоритету)

### P0 — ломает запуск/продукт
- [x] ✅ v28: **Репозиторий содержал 72 отслеживаемых артефакта в `output/` (~262MB WAV/JSON)** — засорял clone, раздувал ZIP. → Добавлен `release/`, `*.zip`, `models/rvc_forks/` в .gitignore; артефакты удалены из индекса (файлы на диске сохранены).
- [ ] **P0: God Mode `run_god_pipeline` падал при `wizard_state=None`** — v28 добавлена защита (Optional[dict] + дефолт), но **полный E2E до master.wav в sandbox не подтверждён** (heavy-deps: phonk/cyber synth). На Windows-цели прогнать `main.py --god --genre drift_phonk` и проверить `output/god_cli/`.

### P1 — критично для пайплайна/голоса/бита
- [ ] **P1: Нет сборки Windows EXE.** GitHub Actions имеет только `ci.yml` (pytest). Нужен `build.yml` (PyInstaller, windows-latest, trigger on push to main) — пользователь должен получать EXE из Actions. v28: подготовить workflow.
- [ ] **P1: `voice_cleaner` = FALLBACK_ONLY** — noisereduce опционален, но не проверен на Windows. Установить на целевой ПК, перевести в REAL_PASS.
- [ ] **P1: `musicgen_texture` = BLOCKED** — audiocraft heavy, не установлен. Подготовить честную инструкцию установки + авто-проверку при старте (сейчас молча падает в лог).

### P2 — качество результата
- [ ] **P2: `voice_synth` = FALLBACK_ONLY** — только pyttsx3/gtts scaffold. Цель: Silero TTS v3.1 RU на CPU (~50MB, реально для RX580/16GB). Обвязка есть, движок не подтверждён.
- [ ] **P2: RVC-конверсия тембра = NOT_TESTED** — `rvc_manager.py` обвязка есть (Applio/Mangio форки), но конверсия на реальной модели не прогонялась. Проверить inference на готовой .pth без обучения.
- [ ] **P2: mastering без true-peak limiting** — сейчас RMS-эквивалент (pyloudnorm LUFS если установлен). Добавить true-peak ceiling -1 dBTP для streaming-стенда.
- [ ] **P2: 82 `except: pass` в modules/ + app/core/** — часть легитимна (опциональные heavy-deps), часть — скрытые падения. Точечно: master_pipeline_v12.py, release_pack_full.py.

### P3 — UI/полировка/cleanup
- [ ] **P3: PySide6 GUI = NOT_TESTED на Windows** — в sandbox невозможно. Проверить `main.py --desktop` на целевом ПК.
- [ ] **P3: smoke_v14..v25 в tools/** — 12 версионных smoke-скриптов. Оставить smoke_v26 (актуальный) + real_e2e_v14, остальные — кандидаты на архив в docs/legacy/.
- [ ] **P3: AUDIT_50_DEEP.md / AUDIT_AND_IMPROVEMENT_REPORT.md / AIDER_GENERATION_AUDIT.md** — исторические аудиты, источник истины = этот файл + PROJECT_STATE. Перенести в docs/legacy/.

---

## ЖУРНАЛ СЕССИЙ

### v28 (2026-08-12) — session-cleanup-godmode-ci-build
**Что проверено:**
- `main.py --version` → REAL_PASS (v27.0.0, version.json читается)
- `pytest tests/` → 7/7 PASS
- `tools/smoke_v26.py` → 6/6 PASS (stereo/loudness/drop/hit_score/hook)
- `orchestrator_god` import → OK; **E2E-прогон выявил крах** при wizard_state=None

**Что исправлено:**
1. **[P0] Репозиторий раздут артефактами** — 72 файла output/ (~262MB) в git-индексе. Расширен .gitignore (release/, *.zip, models/rvc_forks/, бинарники RVC), git rm --cached.
2. **[P0→P1] God Mode краш при wizard_state=None** — `run_god_pipeline(pid, None)` падал на стадии ai_arrangement (`'NoneType'.get`). Теперь Optional[dict] с безопасным дефолтом — пайплайн не умирает на первой стадии при вызове из GUI/smoke без wizard.
3. **[P1] CI не собирает EXE** — добавлен `.github/workflows/build.yml`: Windows runner, PyInstaller, trigger on push to main, artifact upload. Пользователь получает EXE из GitHub Actions.
4. **[Правило 11] Создан этот SESSION_LOG.md** — единый журнал ошибок/доработок/планов.

**Что не удалось:**
- Полный E2E God Mode до master.wav в sandbox: heavy-синтезаторы (phonk_v2/cyber) требуют проверки на целевом Windows. Обвязка исправлена, статус PARTIAL.
- EXE-сборка не верифицирована в sandbox (нет Windows) — NOT_TESTED до первого прогона Actions.

**Оценка:** проект стал лучше — клон на ~260MB легче, God Mode не падает на старте, появился путь к автосборке EXE, заведён канонический журнал.

### v27 (2026-08-12) — mastering-module-stereo-import-fallback
- Создан отсутствующий `modules/mastering.py` (мастеринг всегда падал) ✅
- voice_cleaner: noisereduce → ленивый импорт + fallback ✅
- plugins/advanced: pedalboard/audiomentations ленивые ✅
- mastering_stands: убран монодаунмикс ✅

---

## ПЛАН СЛЕДУЮЩЕЙ СЕССИИ (v29)
1. Проверить результат build.yml в Actions → если EXE собрался, статус REAL_PASS; если упал — чинить spec/пути.
2. Прогнать God Mode E2E на Windows до master.wav.
3. voice_synth: подтвердить Silero на CPU → REAL_PASS.
4. Архивировать smoke_v14..v25 и старые аудиты в docs/legacy/.

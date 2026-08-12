# ZS Music Maker — PROJECT_STATE (канонический журнал)

> Единый источник правды о состоянии проекта. Обновляется каждой сессией.
> README/CHANGELOG/старые аудиты — НЕ источник истины, если расходятся с кодом.

## Текущая версия
- **v27.0.0** — `v27-mastering-module-stereo-import-fallback-2026-08-12`

## Статусы модулей (легенда: REAL_PASS / PARTIAL / FALLBACK_ONLY / BLOCKED / FAILED / MISSING / NOT_TESTED)

| Модуль | Статус | Комментарий |
|---|---|---|
| main.py entry | REAL_PASS | `--version` работает, версии из version.json |
| orchestrator (core) | REAL_PASS | полный пайплайн до release |
| orchestrator_god | FIXED→PARTIAL | был FAIL (noisereduce/pedalboard жёсткие импорты) — исправлено |
| mastering (NEW) | FIXED→REAL_PASS | создан modules/mastering.py, раньше стадия всегда падала |
| mastering_stands | FIXED | убран монодаунмикс (стерео) |
| voice_cleaner | FALLBACK_ONLY | noisereduce опционален, fallback=highpass+DC |
| beat_constructor | REAL_PASS | стерео float32, corr≈0.96, drop-fade есть |
| hit_scorer | REAL_PASS | score_track вызывается, fallback честный |
| voice_synth | FALLBACK_ONLY | torch/TTS/bark/pyttsx3/gtts отсутствуют → scaffold |
| musicgen_texture | BLOCKED | audiocraft не установлен (heavy) |
| RVC | NOT_TESTED | heavy, требует GPU-модели — обвязка есть |

## Выявленные и исправленные проблемы (v27)
1. **[P0] MISSING modules/mastering.py** — мастеринг всегда падал, мастера не создавались. → Создан реальный DSP-модуль. ✅
2. **[P0] Жёсткий import noisereduce** в voice_cleaner → крашил orchestrator_god. → Ленивый импорт + fallback. ✅
3. **[P0] Жёсткий import pedalboard/audiomentations** в plugins/advanced. → Ленивые импорты + no-op. ✅
4. **[P1] mastering_stands монодаунмикс** — убивал стерео. → Каналонезависимый EQ. ✅

## Backlog (следующие сессии, по приоритету)
- [ ] **P1** Полный прогон orchestrator_god E2E на реальном треке (после фикса импортов).
- [ ] **P1** Установить/проверить noisereduce+pedalboard на Windows-цели → перевести voice_cleaner/plugins в REAL_PASS.
- [ ] **P1** musicgen_texture: audiocraft heavy — подготовить честный BLOCKED/инструкцию установки.
- [ ] **P2** voice_synth: реальный Silero/XTTS на CPU baseline (RX580/16GB) — сейчас только scaffold.
- [ ] **P2** RVC-конверсия тембра: проверить обвязку rvc_manager на реальной модели.
- [ ] **P2** mastering: добавить true-peak limiting + LUFS-gating (сейчас RMS-эквивалент).
- [ ] **P3** UI: PySide6 GUI smoke на Windows (не тестировано в sandbox).
- [ ] **P3** cleanup: старые AUDIT_*.md / smoke_v14..v25 — кандидаты на архив.

## Как прогнать проверку
```
python3 main.py --version
python3 tools/smoke_v26.py
python3 -m pytest tests/ -q
```

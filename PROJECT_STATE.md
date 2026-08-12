# ZS Music Maker — PROJECT_STATE (канонический журнал)

> Единый источник правды о состоянии проекта. Обновляется каждой сессией.
> README/CHANGELOG/старые аудиты — НЕ источник истины, если расходятся с кодом.

## Текущая версия
- **v29.0.0** — `v29-god-mode-e2e-midi-fix-truepeak-2026-08-12`

## Статусы модулей (легенда: REAL_PASS / PARTIAL / FALLBACK_ONLY / BLOCKED / FAILED / MISSING / NOT_TESTED)

| Модуль | Статус | Комментарий |
|---|---|---|
| main.py entry | REAL_PASS | `--version` работает, версии из version.json |
| orchestrator (core) | REAL_PASS | полный пайплайн до release |
| orchestrator_god | **REAL_PASS** | v29: E2E завершается `completed`, master_god.wav создан (stereo, 120с, -1 dBTP) |
| midi_generator | **REAL_PASS** | v29: guard в melody + расширенные паттерны phonk/trap/techno, honest BLOCKED без mido |
| mastering_pro | **REAL_PASS** | v29: true-peak -1 dBTP, honest output metrics, mono→stereo, NaN/Inf guard |
| mastering (modules) | REAL_PASS | создан в v27 |
| mastering_stands | REAL_PASS | стерео EQ (без монодаунмикса) |
| voice_cleaner | FALLBACK_ONLY | noisereduce опционален, fallback=highpass+DC |
| beat_constructor | REAL_PASS | стерео float32, corr≈0.96, drop-fade есть |
| cyber_synth | REAL_PASS | FM/Wavetable синтез + Pedalboard FX |
| chanson_engine | REAL_PASS | acoustic guitar + drums + arrangement |
| hit_scorer | REAL_PASS | score_track вызывается, honest fallback |
| voice_synth | FALLBACK_ONLY | torch/TTS/bark/pyttsx3/gtts отсутствуют в sandbox → scaffold |
| musicgen_texture | BLOCKED | audiocraft heavy, не установлен |
| RVC | NOT_TESTED | heavy, требует GPU-модели — обвязка есть |
| PySide6 GUI | NOT_TESTED | Windows-only, sandbox не поднимает Qt |
| Windows EXE build | NOT_TESTED | .github/workflows/build.yml готов, ждём прогон Actions |

## Sanity/smoke метрики (v29)
- `pytest tests/` → **7/7 PASS**
- `tools/smoke_v26.py` → **6/6 PASS** (stereo/loudness/drop/hit_score)
- `tools/smoke_v29.py` → **8/8 PASS** (God Mode E2E + midi + mastering_pro)

## Backlog (следующая сессия v30)
- **P1** Проверить результат `.github/workflows/build.yml` после push v29 (EXE, Windows Actions).
- **P1** voice_cleaner + noisereduce на Windows → REAL_PASS.
- **P1** musicgen_texture: honest BLOCKED-детектор при старте.
- **P2** voice_synth: реальный Silero v3.1 RU на CPU baseline.
- **P2** RVC inference на готовой .pth.
- **P2** mastering: LUFS-gating опция + референс-матчинг (matchering).
- **P3** cleanup: точечно почистить `except: pass` в master_pipeline_v12.py.

## Как прогнать проверку
```bash
python3 main.py --version
python3 tools/smoke_v26.py
python3 tools/smoke_v29.py
python3 -m pytest tests/ -q
```

## Как получить Windows EXE
1. Push в `main` уже запускает `.github/workflows/build.yml`.
2. Открыть https://github.com/ttklon/ZS-MUSIC-MAKER/actions
3. Найти последний прогон workflow `Build Windows EXE` на коммите v29.
4. Скачать артефакт `ZS-Music-Maker-Windows-EXE` (retention 30 дней).

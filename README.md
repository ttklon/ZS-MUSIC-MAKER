# ZS Music Maker «Hit Locked Pro»

> **Актуальная версия:** v37.0.0 (2026-08-14) — единый источник правды: `version.json`.
> **Статус:** Production Ready (аудио-ядро beat→mix→mastering→God Mode — REAL_PASS).

## 🎯 Главная цель

Создавать **хитовые треки**, которые качают в тачках, звучат в клубах и
TikTok — полностью **бесплатно**, **автономно**, **автоматизированно**
и **локально** на ПК пользователя.

## ⚡ Что нового в v36

- **README/CHANGELOG unification** — вычищены протухшие блоки «Что нового в v14/v17/v18» и битые ссылки на перенесённые в `docs/legacy/` smoke-скрипты (v14/v15/v17/v18/v21/v24/v25). Раздел «Тесты» и таблица статусов приведены к текущему v35+ ядру.
- **FIX P1 `main.py --smoke`** — цепочка fallback чистилась от мёртвых имён (`tools.smoke_v14/v15/v17/v21/v24/v25` — они в `docs/legacy/`). Теперь только реально запускаемые `smoke_v29` → `smoke_v26`.
- **FIX P2 silent-except** — `app/plugins/base.py` (Sanitizing warning) и `app/core/cover_gen.py` (font-load loop) больше не глотают ошибки полностью — логируют причину.
- **FIX P1 `build.yml` (PyInstaller)** — добавлены критичные `--add-data models`, `data/genre_presets`, `data/prompts`, а также `--collect-submodules modules|app|agents|tools|ui|updater` вместо мёртвого `--hidden-import`. Смок-шаг проверки EXE больше не `continue-on-error: true` — падение сборки будет видно.
- **Cleanup** — устаревший «v10 Chart Killer Pro» заголовок и упоминание несуществующего `windows_build.bat` убраны из `requirements.txt`; `INSTALL.md` и `PROJECT_STATE.md` приведены к v36.

## ⚡ Что нового в v35 (архив, полная история — SESSION_LOG.md)

- **REAL_PASS `voice_synth` Silero TTS** — RU v3.1, female=kseniya, живой WAV 48kHz.
- **P1 `musicgen_texture`** — honest `detect_availability()` / `get_status()` вместо молчаливого падения.
- **P2 silent-except** — точечно почищены `master_pipeline_v12` и `release_pack_full`.
- **Cleanup git-индекса** — мёртвый `safe_import.py`, чужие снапшоты health/kpi, дубль `tutorial_settings.json`.

## 🚀 Быстрый старт

```batch
run.bat                     :: главный запуск (Windows)
python main.py --god        :: God Mode: полный пайплайн одной командой
python main.py --smoke      :: smoke (v29 God Mode E2E → v26 audio quality)
python main.py --dry-run    :: полный dry-run пайплайна без тяжёлых моделей
python main.py --dashboard  :: KPI-дашборд с % готовности ТЗ
python main.py --health     :: health-check стека
python main.py --readiness  :: честный %
python main.py --version    :: версия/билд (из version.json)
python main.py --console    :: headless-режим
```

Если PySide6 недоступен — падает в Gradio (127.0.0.1:7860),
если и Gradio нет — в интерактивный console-режим.

## 🧪 Тесты и smoke

```bash
python -m pytest tests/                    # DSP-юниты (7/7 PASS)
python tools/smoke_v26.py                  # аудио-качество (stereo/loudness/drop/hit-score) — 6/6 PASS
python tools/smoke_v29.py                  # God Mode E2E → master_god.wav — 8/8 PASS
python tools/fallback_audit.py             # honesty-scan (red_flags=0)
```

Устаревшие smoke_v14..v25 перенесены в `docs/legacy/` — по старым путям их
намеренно нет, чтобы не создавать иллюзию «свежих» тестов.

## 🎧 Что честно, а что BLOCKED (v36)

| Слой                 | Статус             | Комментарий                                        |
|----------------------|--------------------|----------------------------------------------------|
| main / CLI           | REAL_PASS          | версия из version.json, --smoke → v29/v26          |
| analyzer / groove    | REAL_PASS          | librosa-based                                      |
| beat_constructor     | REAL_PASS          | реальный construct_beat wiring (v17+)              |
| lyrics_gen (LLM)     | PARTIAL / FALLBACK | LLM цепочка есть, fallback = punch-lib             |
| voice_synth (Silero) | REAL_PASS          | RU v3.1, kseniya/aidar, CPU, WAV 48kHz (v35)       |
| RVC                  | BLOCKED без .pth   | pitch-shift-fallback ЗАПРЕЩЁН (ТЗ 33.5)            |
| mix + sidechain      | REAL_PASS          | реальный bus + ducking (v17+)                      |
| mastering_pro        | REAL_PASS          | true-peak -1 dBTP, NaN/Inf-guard, mono→stereo (v29)|
| midi_generator       | REAL_PASS          | mido-паттерны phonk/trap/techno, honest BLOCKED    |
| anti-neuro polish    | REAL_PASS          | pydub-полный или numpy-fallback                    |
| stems (demucs)       | BLOCKED без demucs | опциональная тяжёлая зависимость                   |
| musicgen_texture     | BLOCKED без audiocraft | honest detect_availability() (v35)             |
| hit_scorer           | REAL_PASS          | librosa-based                                      |
| release_pack         | REAL_PASS          | full-pack (~38 файлов) или minimal fallback        |
| God Mode E2E         | REAL_PASS          | 5 стадий → master_god.wav 120с stereo -1 dBTP      |

## ⚠️ Требования к железу (baseline)

- Xeon 2.5 GHz v2 (или аналог)
- AMD RX 580 4 ГБ (DirectML) / NVIDIA CUDA / CPU
- 16 ГБ RAM
- Windows 11

Всё, что не влезает в baseline, честно помечено BLOCKED и не роняет
пайплайн.

## 📝 Лицензия

MIT — см. [LICENSE](./LICENSE).

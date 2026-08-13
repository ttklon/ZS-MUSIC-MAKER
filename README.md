# ZS Music Maker «Hit Locked Pro»

> **Актуальная версия:** v33.0.0 (2026-08-13) — единый источник правды: `version.json`.
> **Статус:** Production Ready (аудио-ядро beat→mix→mastering→God Mode — REAL_PASS).

## 🎯 Главная цель

Создавать **хитовые треки**, которые качают в тачках, звучат в клубах и
TikTok — полностью **бесплатно**, **автономно**, **автоматизированно**
и **локально** на ПК пользователя.

## ⚡ Что нового в v26 (Pro Audio DSP + Quality Gate)

- **NEW `modules/pro_audio_dsp.py`** — Профессиональный движок цифровой
  обработки сигналов. Фазовое выравнивание стереоканалов, мягкое
  лимитирование через сатурацию (True Peak) и точный LUFS-мастеринг.
- **Quality Gate (`tools/quality_gate.sh`)** — Строгий контроль качества
  кода (Pylint 10/10, Mypy, Pytest). Теперь проект соответствует стандартам
  ведущих AI-кодеров (Claude Code, Genspark).
- **100+ Музыкальных жанров** — Расширенная поддержка жанров с уникальными
  профилями мастеринга и BPM.
- **Исправление архитектуры (Category D)** — Удален мертвый код, очищен
  репозиторий от бинарного мусора, внедрена безопасная сериализация JSON.

## ⚡ Что нового в v18 (вокал + честность fallback)

- **NEW `modules/vocal_fx.py`** — настоящий vocal double-tracking +
  delay throw на концах фраз (VAD). Честный numpy-DSP, не нейросеть,
  не заглушка. Даёт хуку плотность и «воздух» до микса.
- **Оркестратор: стадия `_stage_vocal_fx`** — между RVC и миксом.
  При сбое — честный bypass, пайплайн не ломается.
- **`sidechain.py` без scipy** — numpy FFT bandpass onset-detector:
  ducking-метрика больше не молча 0 на слабом железе (7.4 dB со scipy,
  6.6 dB без).
- **`mixdown.py`** — честный статус matchering (`used_matchering` /
  `fallback_used` / `engine`), copy больше не выдаётся за мастеринг.
- **`tools/fallback_audit.py`** — регресс-страж `apply_sidechain(x,x)`,
  метка `ZSMM_NOT_RVC`, детекция hard-refusal. **red_flags = 0.**
- **`tools/smoke_v18.py`** — 6/6 PASS; добавлен в run_all_smoke.

## ⚡ Что нового в v17 (P0-фиксы главного пайплайна)

v17 — это НЕ косметика, это фиксы в самом пайплайне, из-за которых
предыдущие сборки выдавали заметно более слабый WAV, чем могли:

- **P0.01 — beat wiring**: `_stage_beat` искал несуществующую
  `beat_constructor.build_beat` → в 100% случаев тихо падал в
  упрощённый `_synth_beat`. Теперь корректно вызывает
  `beat_constructor.construct_beat(...)` с groove/style_vector.
- **P0.02 — lyrics wiring**: `_stage_lyrics` возвращал `text`, а
  оркестратор читал `lyrics` → в трек попадала пустая строка,
  вокал синтезировался «в ноль», release_pack без лирики.
  Теперь стадия ВСЕГДА возвращает и `text`, и структурированный
  `lyrics` (title / verse1 / chorus / verse2).
- **P0.03 — mix bus (главный аудио-баг)**: `_stage_mix_and_sidechain`
  дакал бит САМ СОБОЙ (`apply_sidechain(beat, beat, ...)`) и
  ВООБЩЕ не подмешивал вокал в bus. В итоге в мастер шёл голый
  бит, вокала не было слышно. Теперь честный микс `bus = beat + vocal`
  (ресемпл, HP80 Гц на вокале, авто-гейн), потом sidechain по кику.
- **P0.04 — anti-neuro polish**: `_stage_polish` искал `apply_polish`,
  а модуль экспортирует `polish_vocal`. Стадия НИКОГДА не
  выполнялась — всегда `shutil.copy`. Теперь есть и `apply_polish`,
  и `polish_vocal`, и **честный numpy-fallback** (soundfile+scipy:
  breath, hi-shelf, low-pass ghost-remove, fade-out, human-error) —
  работает даже без pydub.
- **P0.05 — version drift**: `main.py` печатал `v14.0.0`, а
  `version.json` был `v16.0.0`. Теперь `VERSION`/`BUILD` читаются
  ИЗ `version.json` — один источник правды.
- **P0.06 — консольная кодировка**: логика была инвертирована —
  на UTF-8 консоли Windows Terminal / PowerShell 7 stdout насильно
  оборачивали в cp866 → русские буквы становились кракозябрами.
  Теперь UTF-8 не трогаем, cp866 только как последний шанс.
- **smoke_v17** — 6 новых целевых проверок именно этих P0-фиксов,
  включая mini-E2E проверку, что после mix bus RMS реально выше
  RMS одного бита ⇒ вокал попал в bus.

## 🚀 Быстрый старт

```batch
run.bat                     :: главный запуск (Windows)
python main.py --smoke      :: smoke (v17 + v14)
python main.py --dry-run    :: полный dry-run пайплайна без тяжёлых моделей
python main.py --dashboard  :: KPI-дашборд с % готовности ТЗ
python main.py --health     :: health-check стека
python main.py --readiness  :: честный %
python main.py --version    :: версия/билд (из version.json)
python main.py --console    :: headless-режим
```

Если PySide6 недоступен — падает в Gradio (127.0.0.1:7860),
если и Gradio нет — в интерактивный console-режим.

## 🧪 Тесты v17

```bash
python3 tools/smoke_v26.py   # аудио-качество (stereo/loudness/drop/hit-score)
python3 tools/smoke_v29.py   # God Mode E2E до master_god.wav
# v33: smoke_v14/v17 перенесены в docs/legacy/ — по старым путям их нет
```

## 🎧 Что честно, а что BLOCKED в v17

| Слой                 | Статус v17         | Комментарий                                        |
|----------------------|--------------------|----------------------------------------------------|
| main / CLI           | REAL_PASS          | версия из json, encoding un-inverted               |
| analyzer / groove    | REAL_PASS          | librosa-based                                      |
| beat_constructor     | REAL_PASS          | v17: реальный construct_beat wiring                |
| lyrics_gen (LLM)     | PARTIAL / FALLBACK | LLM цепочка есть, fallback = punch-lib             |
| voice_synth          | PARTIAL            | требует silero/xtts/pyttsx3 на ПК                  |
| RVC                  | BLOCKED без .pth   | pitch-shift-fallback ЗАПРЕЩЁН (P0.05 TZ 33.5)      |
| mix + sidechain      | REAL_PASS          | v17: реальный bus, реальный ducking                |
| mastering 8 стендов  | REAL_PASS/PARTIAL  | matchering→pedalboard→numpy→pydub(gain)            |
| anti-neuro polish    | REAL_PASS          | v17: pydub-полный или numpy-fallback               |
| stems (demucs)       | BLOCKED без demucs | опциональная тяжёлая зависимость                   |
| hit_scorer           | REAL_PASS          | librosa-based                                      |
| release_pack         | REAL_PASS          | full-pack (~38 файлов) или minimal fallback        |

## ⚠️ Требования к железу

- Xeon 2.5 GHz v2 (или аналог)
- AMD RX 580 4 ГБ (DirectML) / NVIDIA CUDA / CPU
- 16 ГБ RAM
- Windows 11

Всё, что не влезает в baseline, помечено BLOCKED и не роняет пайплайн.

## 📝 Лицензия

MIT — см. [LICENSE](./LICENSE).

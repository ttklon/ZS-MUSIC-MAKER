# HIT FACTORY — Быстрый старт (бесплатно, нероншно, как человек)

## 1. Что это

Одной командой генерит **завершённый трек** (бит + текст + вокал TTS/инструментал + микс + 8 мастеров + hit_score) без платных API и тяжёлых моделей.  
Поверх классического пайплайна — **эволюционная петля**: сгенерил → измерил `hit_score` (12 метрик) → мутировал `BPM/aggression/seed` → выбрал лучшего.

- **Бесплатно**: `numpy/scipy/soundfile/librosa` + 32 CC0 сэмпла 808/BOOCHI44, шаблонные тексты, `pyttsx3`/`gTTS` фолбэк, `anti_neuro` на `numpy`. Тяжёлые модели `ACE-Step/MusicGen/RVC/Demucs/SDXL` опциональны и не нужны для хита (будет `BLOCKED` честно).
- **Нероншно**: `humanize` (микротайминг ±9мс, swing, velocity ±12%, ghost 0.28, round-robin сэмплов) + `anti_neuro` (дыхания в паузах, микропровалы −6…−10дБ, детюн ±4 cents, `de_plastic`, `consonant_boost`).
- **Как человек**: дроп-пауза 300мс**4 перед hook, hook-лид из 4 нот в intro+chorus, 4-по-4 структура, sidechain, стерео-ширина 0.6–0.85.

## 2. Установка (1 раз)

```bat
scripts\setup.cmd          # Windows 11 — проверит Python 3.11+, venv, deps, health
# или Linux/Mac
python -m pip install -r requirements.txt --break-system-packages
```

Для голосового вокала (опционально, иначе будет инструмент):
```bat
# Linux: eSpeak для pyttsx3
sudo apt-get install espeak
# или запиши свой голос в визарде — это основной путь (own_vocal_wav)
```

## 3. Запуск

### Через лаунчер (самый простой)
```bash
python hitmaker.py --help

# 1 случайный хит (жанр/тема/BPM — авто из трендов 2026 offline)
python hitmaker.py

# 1 хит в стиле trap про ночь
python hitmaker.py --genre trap --theme "ночь, деньги, движ" --seed 42 --duration 90

# 5 хитов батчем, эволюция включена (≤3 попытки на трек, порог 68=solid)
python hitmaker.py --count 5 --evolve --min-score 68

# 10 хитов по 65 сек (тикток-формат), без эволюции (быстро)
python hitmaker.py --count 10 --duration 65 --no-evolve

# детерминизм: одинаковый seed+жанр+тема = побайтово тот же бит
python hitmaker.py --genre drift_phonk --theme "лето, тачки, Стамбул" --seed 123 --duration 120
```

### Через главный CLI
```bash
python main.py --hit-factory --hit-count 3 --hit-genre phonk --hit-theme "ночь, неон"
python main.py --hit-factory --hit-count 1 --hit-seed 42 --hit-duration 90 --hit-min-score 68
python main.py --hit-factory --hit-count 5 --hit-genre trap --hit-no-evolve
```

### Через Python API
```python
from modules.hit_factory import HitFactory, quick_hit

# один хит
hit = quick_hit(theme="лето, тачки, Стамбул", genre="drift_phonk", seed=42)
print(hit["hit_score"], hit["verdict"], hit["master_path"])

# фабрика
factory = HitFactory(output_root="output/hits", min_score=68, evolve=True, max_attempts=3, duration_sec=120)
batch = factory.make_batch(count=5)               # 5 случайных хитовых жанров
batch = factory.make_batch(count=3, genre="trap") # 3 trap хита
```

## 4. Куда смотреть результат

```
output/hits/
  hit_trap_20261114_075805_71b86c/
    beat.wav                    # бит (стерео, humanized)
    mix.wav                     # микс (bus −18 dBFS, sidechain, width)
    masters/
      master_streaming.wav      # основной мастер (−14 LUFS, true-peak ≤−1 dBTP)
      master_streaming_human.wav # +anti_neuro_track polish (нероншно)
      master_tiktok.wav / master_club.wav / ...
    tiktok/
      tiktok_15s.wav            # 15с вирусный кусок (hit_scorer tiktok_slice)
      tiktok_30s.wav            # 30с для Reels/Shorts
      hook_loop.wav             # только припев для эдитов
    cover.png                   # обложка 1400x1400 PIL (gradient/neon/glitch по жанру)
    report.json                 # полный отчёт 15 стадий + tiktok_cuts + cover
    hit_report.json             # hit_score + 12 метрик + actions
    factory_summary.json        # если эволюция — все попытки + лучший
  batch_20261114_075900_*.json  # индекс батча
  hits_kpi.json / hits_kpi.md   # агрегат KPI по всем хитам (avg, genre, best/worst)
  benchmark_20261114_*.json     # отчёт A/B бенчмарка по жанрам
```

Оценка:
```bash
python main.py --score output/hits/<id>/masters/master_streaming.wav
# hit_score 72.43 solid → хорошо, 56 needs_work → мутируй/перегенери
python -m modules.hit_factory.kpi              # пересчитать KPI (avg, genre, best)
python -m modules.hit_factory.benchmark --genres drift_phonk,trap --count 2 --duration 30  # A/B по жанрам
```

Оценка:
```bash
python main.py --score output/hits/<id>/masters/master_streaming.wav
# hit_score 72.43 solid → хорошо, 56 needs_work → мутируй/перегенери
```

## 5. Вирусная формула (что подкрутить для хита)

| Проблема в `hit_report.actions` | Что делать фабрике |
|---|---|
| Припев тише куплета | поднять `aggression` 0.8+ или `duration 120` (chorus gain 1.0 vs verse 0.7) |
| Повторяй мотив ≥3 | не трогай — hook-лид уже повторяется 4 ноты × бара |
| BPM вне dance | выбери `jersey_club 138`, `phonk 140`, `trap 144/72`, `house 126` |
| LUFS вне target | мастер уже целит −14 streaming / −8.5 club, проверяй `report.json` громкость |
| Vocal presence | установи `eSpeak` или запиши свой вокал — scaffold не миксуется специально |
| Секции похожи | `aggression` выше + `anti_neuro_track` entropy_boost (вторая половина ≠ первая) |

Фабрика делает это автоматически при `--evolve`.

## 6. Автоматизация по расписанию + KPI + Бенчмарк

```bash
# Linux cron: каждые 6 часов по 2 хита
crontab -e
# 0 */6 * * * cd /path/to/ZS-MUSIC-MAKER && python hitmaker.py --count 2 --evolve >> logs/hits.log 2>&1

# Демон (бесконечный, с авто-трендом 24ч и KPI):
python -m modules.hit_factory.daemon --interval 6 --count 2
# или из Python:
from modules.hit_factory.daemon import run_daemon
run_daemon(interval_hours=6, count_per_run=2, genre="phonk")

# A/B бенчмарк жанров (тюнинг весов):
python -m modules.hit_factory.benchmark --genres drift_phonk,trap,phonk,jersey_club --count 2 --duration 30
# → output/hits/benchmark_*.json + таблица avg/max/solid_rate и рекомендации

# KPI агрегат:
python -m modules.hit_factory.kpi               # консоль + hits_kpi.md
python -m modules.hit_factory.kpi --json       # json в stdout
cat output/hits/hits_kpi.md
```

## 7. FAQ

**Почему без вокала?**  
Свободный `pyttsx3` требует `eSpeak`, `gTTS` — интернет к `translate.google`. Без них вокал = `rap_scaffold` (формантный шаблон) и он **намеренно не миксуется** (иначе пластмасса). Решение: `apt install espeak` или запиши свой голос в визарде (`own_vocal_wav` — главный путь).

**Почему hit_score 56 needs_work?**  
Короткий трек 20–30с + инструментал без вокала = низкие `hook_repeatability`/`vocal_presence`. Полный 90–120с с вокалом даёт `68+ solid`. Используй `--duration 90 --evolve --min-score 68`.

**Нужен ли GPU?**  
Нет. Фабрика — чистый CPU/DSP. GPU нужен только для опциональных `ACE-Step/RVC/Demucs/SDXL`.

**Детский вопрос: это точно бесплатно?**  
Да. Всё из `requirements.txt` wheels + CC0 сэмплы. Никаких ключей OpenAI/Grok/Gemini/Reddit не нужно (trend_scout работает offline fallback если сети нет).

**Где план развития?**  
`docs/HIT_FACTORY_PLAN.md` — 5 фаз от скелета до масштаба + KPI dashboard.

**Видео?**  
Если установлен `ffmpeg` — фабрика делает `tiktok/tiktok_15s.mp4` (9:16, обложка+аудио). Без `ffmpeg` — пропускает, трек всё равно готов.

**Автотюнинг?**  
```bash
python -m modules.hit_factory.autotune            # рекомендации по весам жанров
python -m modules.hit_factory.autotune --apply    # переписать HIT_GENRE_WEIGHTS в config.py
python -m modules.hit_factory.ui                  # Gradio веб-UI: один хит / батч / KPI
```

**Релиз и слепое прослушивание?**
```bash
python -m modules.hit_factory.release             # лучший хит → output/releases/<id>/
python tools/blind_listening_prep.py --hits 5     # output/blind_test/01..10.wav + _key.txt
# затем слушай по docs/BLIND_LISTENING.md и заполни docs/BLIND_LISTENING_RESULT.md
```

---
ZS Music Maker HIT FACTORY v1.3 — 2026-11-14 (release+blind+demo 78.8)

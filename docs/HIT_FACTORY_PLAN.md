# HIT FACTORY — Автономная фабрика хитов ZS Music Maker
> Версия 1.0 — 2026-11-14. Полностью бесплатно. Нероншно. Как человек.

## 0. TL;DR — что это

**HIT FACTORY** — надстройка над классическим DSP-пайплайном `ZS Music Maker`, которая превращает одиночный прогон (`run_full_pipeline`) в **автономную фабрику хитов**:

- сама придумывает тему / жанр / BPM по вирусным формулам 2026
- сама генерит 1..N треков без участия человека (батч)
- сама меряет `hit_score` и эволюционирует, пока не пробьёт порог `solid` / `chart_ready`
- остаётся **100% бесплатно**: только `numpy / scipy / soundfile / librosa` + CC0 сэмплы 808/BOOCHI44, без платных API и тяжёлых моделей
- звучит **не как нейросеть**: `humanize` (микротайминг ±9мс, swing, velocity ±12%, ghost-ноты) + `anti_neuro` (дыхания в паузах, микропровалы, de-plastic, consonant boost) + драматургия секций

Запуск:
```bash
python hitmaker.py --count 5              # 5 хитов подряд, авто-темы
python hitmaker.py --genre trap --theme "ночь, деньги, движ" --count 3
python -m modules.hit_factory --count 10 --evolve --min-score 68
python main.py --hit-factory --count 3    # через главный CLI
```

Результат: `output/hits/<id>/master.wav` + `report.json` + `hit_report.json` + релиз-пакет.

---

## 1. Анализ исходного репозитория (суть работы)

### 1.1 Что уже есть (реальность v41.0.0-alpha.16)

| Слой | Статус | Бесплатно? | Человечность |
|---|---|---|---|
| **Beat** `modules/beat/*` + `data/samples` 32 CC0 one-shot'а (TR-808 Фишер + BOOCHI44) + `SampleBankMixin` | `REAL_PASS` — барабаны из банка, саб/дроп — синтез | ✅ да | `humanize.py` (PART_FEEL_MS, ACCENT, ghost, variant, swing) |
| **Lyrics** `modules/lyrics/*` + `lyric_vault/slang.txt` + `trend_scout` (DuckDuckGo/Reddit + offline fallback 2026) | LLM → Ollama → punchline-библиотека → шаблон | ✅ offline шаблон бесплатен | hook repeat, bilingual (RU верс + EN hook) |
| **Vocal** `app/core/stages/vocal*` → Silero/XTTS/bark → `pyttsx3` → `rap_scaffold_numpy_v22` (формантный scaffold) | BLOCKED честный без TTS, scaffold только как placeholder (RVC заблокирован для scaffold) | ✅ pyttsx3/scaffold бесплатны | `anti_neuro.py` (breaths_in_pauses, human_error, de_plastic) |
| **Mix** `modules/mix/bus` (gain staging −18 dBFS, channel EQ, sidechain kick→низ, width) + `reference` (EQ под референсы) | REAL_PASS | ✅ DSP | width, sidechain, reference EQ |
| **Master** `modules/mastering/*` 8 стендов (streaming/tiktok/club/car/...), true-peak ≤−1 dBTP, crest/correlation гейты, parallel ProcessPool | REAL_PASS | ✅ | — |
| **Anti-neuro track** `modules/anti_neuro_track.py` (track polish) | REAL_PASS | ✅ | entropy_boost аналог |
| **Hit Scorer** `modules/hit_scorer/*` 12 метрик (hook_energy, hook_repeatability, chorus_catchiness, drop_impact, tiktok_hookability, bpm_dance_fitness, loudness_lufs, stereo_width, low_end_power, vocal_presence, structure_clarity, novelty) → verdict `chart_ready≥82 / solid≥68 / needs_work≥50 / flop_risk` | REAL_PASS | ✅ | — |
| **Orchestrator** 15 стадий + `recipe.py` + `pipeline_runtime` + `report.json` | PASS_PARTIAL (гейты mix/master/reference часто PARTIAL) | ✅ | — |

**Главный инсайт**: бесплатный путь уже даёт законченный трек 90–120с, MIDI-структуру, микс и мастер. Узкое горлышко хитовости — не отсутствие моделей, а **отсутствие отбора и эволюции**: один прогон даёт один случайный результат без петли `сгенерил → измерил hit_score → улучшил`.

### 1.2 Что мешает хиту сейчас

1. **Нет автономии**: нужен визард, ручной выбор жанра/темы/BPM каждый раз.
2. **Нет петли качества**: `hit_score` считается, но не влияет на следующий прогон.
3. **Нет вирусных формул**: структура секций фиксирована (`intro 4 / verse 8 / pre 4 / chorus 8 ...`), hook не всегда попадает в первые 15 сек, drop не всегда читается.
4. **Нероншно частично**: `anti_neuro` применяется к вокалу, но не к итоговому треку системно; `humanize` есть в бите, но не форсируется как обязательный гейт.
5. **Тема однообразна**: если LLM offline → один и тот же шаблон `Ночь горит`.

### 1.3 Решение: HIT FACTORY как эволюционный отбор поверх бесплатного стека

Не переписываем DSP. Добавляем **тонкий слой оркестрации**:
```
Тема/Жанр/BPM (trend_scout offline+live) →
  Recipe (human offsets) →
    run_full_pipeline (free) →
      hit_scorer →
        if score < threshold → mutate(seed, BPM, aggression) → repeat (≤3)
      → anti_neuro_track extra polish (нероншно) →
        → сохранить лучший из N
```

Цена: 1 трек ≈ 15–40с CPU (без GPU/моделей). 5 треков ≈ 2–3 минуты.

---

## 2. Вирусная формула хита 2026 (бесплатно реализуемая)

Выведена из `modules/hit_scorer` гейтов и `modules/beat/dramaturgy.py`:

| Принцип | Реализация в Factory | Гейт hit_scorer |
|---|---|---|
| **Hook в первые 15 сек** | `intro` ≤4 bars, `hook_lead` (`_mot` из `BeatConstructor`) звучит уже в `intro` + `chorus` (см. `constructor.py:_root/_mot` loop) | `tiktok_hookability` |
| **Повторяемость мотива ≥3** | hook-лид из 4 нот (minor/major пентатоника) повторяется каждую 1/4 такта в hook/chorus | `hook_repeatability` |
| **Дроп = тишина 300мс перед hook** | `full_track[_idx-_fade:_idx] *= env**4` (construct_beat) | `drop_impact` (max RMS jump) |
| **BPM sweet spot** | trap 70–95 / dance/phonk 120–144 / jersey 130–142 / rage 145–160 | `bpm_dance_fitness` |
| **Loud-Quiet контраст** | verse gain 0.7–0.85, chorus gain 1.0, клубный стенд −8.5 LUFS | `hook_energy` |
| **2–3 аккорда в припеве** | `harmony.py`: 4 ноты баса по ступеням лада, мелодия пентатоника | `chorus_catchiness` |
| **Стерео-ширина 0.6–0.85** | `mix/width.py` + pan lead ±0.15 | `stereo_width` |
| **Саб 20–80 Гц** | `synth_808` + sidechain + `low_end_power` | `low_end_power` |
| **Вокал 2–5 кГц читаемость** | `consonant_boost` 3–10 кГц на атаках | `vocal_presence` |
| **Новизна (не формульно)** | `entropy_boost` + `human_error` + `variant_index` round-robin | `novelty`, `structure_clarity` |

Factory форсирует эти цифры выбором `BPM/aggression/genre` и мутациями, а не магией.

---

## 3. Архитектура HIT FACTORY

```
modules/hit_factory/
  __init__.py        публичный API: HitFactory, quick_hit, batch
  config.py          HIT_GENRES (веса), BPM_MAP, THEME_POOL, THRESHOLDS, HUMAN_PRESETS
  themes.py          pick_theme(), pick_genre(), pick_bpm(), inject_slang(), trend_context()
  humanizer.py       ensure_human() — доп. anti_neuro_track + проверка humanize гейтов
  evolver.py         mutate(), select_best() — эволюционная петля
  generator.py       HitFactory — главный класс, вызывает run_full_pipeline + hit_scorer
tools/hit_factory.py CLI батча
hitmaker.py          корневой однострочный лаунчер (для пользователя)
app/cli/hitfactory.py интеграция с main.py --hit-factory
docs/HIT_FACTORY_PLAN.md (этот файл)
```

### 3.1 Поток одного хита

```python
factory = HitFactory(output_root="output/hits", min_score=68, evolve=True)
result = factory.make_one(genre="trap", theme="ночь, деньги, движ", seed=42)
# внутри:
# 1. trend_context(theme) → hype_words/cities/brands → обогащает theme
# 2. genre → BPM sweet spot (или переопределён)
# 3. recipe = build_recipe({...voice_mode: pro, vocal_offset, aggression, duration_sec=90-120})
# 4. run_full_pipeline(project_id, recipe)
# 5. score_track(master.wav) → hit_score
# 6. if evolve and hit_score < min_score: mutate(seed+1, bpm±5, aggression±0.15) × up to 3 → keep best
# 7. humanizer.ensure_human(master.wav) → anti_neuro_track polish (опц.)
# 8. save hit_report.json + return {project_id, hit_score, verdict, master_path, attempts}
```

### 3.2 Батч

```python
factory.make_batch(count=10, evolve=True, parallel=False)
# последовательно (чтобы не ломать Numba кэш: isolated_numba_cache на каждый run),
# прогресс через on_stage колбэк → CLI полоска.
```

### 3.3 Человечность («нероншно»)

Обязательные проверки после каждого прогона (если выключены — включаем и пере-рендерим):
- `humanize`: timing_offset_ms clip ±9мс, velocity_gain 0.88–1.12 + accent 1.09, ghost 0.28, swing на odd 16th
- `anti_neuro vocal`: breaths_in_pauses (вдохи аддитивно в паузах, длина сохранена), human_error (micro dips −6…−10дБ 40мс 3%, detune ±4 cents блоками 0.25с), de_plastic (>15.5кГц −50%), consonant_boost (+3дБ 3–10кГц на атаках)
- `anti_neuro_track`: лёгкая энтропия второй половины (highpass 120Гц) чтобы «второй куплет ≠ копия»
- `dramaturgy`: hook в intro, drop-pause 300мс**4 перед первым hook

Если `humanizer` находит, что стадия была пропущена или FALLBACK без причины — помечает `warnings`.

---

## 4. План работ (5 фаз)

### Фаза 0 — Аудит и фундамент ✅ done (2026-11-14 анализ)
- [x] Прочитан `ARCHITECTURE.md`, `ROADMAP.md`, `PROJECT_STATE.md`, 276 модулей
- [x] Проверен free путь: beat REAL_PASS (sample_bank+procedural), vocal scaffold BLOCKED честно, mix/master/anti_neuro/hit_scorer REAL_PASS
- [x] Зафиксированы гейты hit_scorer и вирусные формулы

### Фаза 1 — Скелет Factory (этот коммит)
- [x] `modules/hit_factory/config.py` — веса хитовых жанров (phonk/trap/jersey/drill/hyperpop/rage/plugg), BPM_MAP, THEME_POOL 2026, THRESHOLDS
- [x] `modules/hit_factory/themes.py` — pick_theme/genre/bpm + trend_scout offline обёртка
- [x] `modules/hit_factory/evolver.py` — mutate + select_best
- [x] `modules/hit_factory/humanizer.py` — ensure_human + доп. polish
- [x] `modules/hit_factory/generator.py` — HitFactory.make_one/make_batch + quick_hit()
- [x] `tools/hit_factory.py` + `hitmaker.py` + `app/cli/hitfactory.py` + флаг `--hit-factory` в parser
- [x] `tests` smoke для factory (детерминизм seed, batch создаёт N папок)

### Фаза 2 — Хит-формула тюнинг (след. итерация)
- [ ] A/B тест 5 жанров × 3 BPM × 3 aggression → измерить hit_score распределение на `output/hits_benchmark`
- [ ] Подкрутить `BPM_MAP` и `GENRE_WEIGHTS` по факту `tiktok_hookability` и `drop_impact`
- [ ] Добавить TikTok edit `modules/tiktok_edit.py` в релиз-пакет factory (15с, 30с, 45с slices)
- [ ] Промпт-инъекция сленга: `actual_slang_for_prompt()` → в `recipe.theme` если LLM доступен (Ollama)

### Фаза 3 — Нероншно MAX
- [ ] Принудительно включать `humanize`+`anti_neuro` даже если пользователь снял галочки (factory режим — всегда human)
- [ ] Добавить `vocal_fx` дубль/throw/pitch детюн по умолчанию (проверено на `voice_synth` scaffold vs pyttsx3)
- [ ] Слепое прослушивание `docs/BLIND_LISTENING.md` на 10 треках factory vs template (5 слушателей)

### Фаза 4 — Полная автономия
- [ ] `HitFactory.daemon(interval_hours=6)` — бесконечный генератор по расписанию (cron внутри `render_queue`)
- [ ] Авто-тренд: `trend_scout.scout(theme)` раз в 24ч → обновляет `THEME_POOL`
- [ ] Telegram/Discord бот нотификация + автозаливка в `output/hits` → `release/pack`
- [ ] KPI Dashboard `modules/kpi_dashboard` — график hit_score во времени, жанр-лидер, проход гейтов

### Фаза 5 — Масштаб и релиз
- [ ] Обложка `cover_art_gen` (SDXL если есть VRAM иначе procedural gradient) в батче
- [ ] Видео-клип `video_edit` + `tiktok_edit` автo-сборка
- [ ] Проверка на Windows 11 + RX 580 + NVIDIA (совместимость Numba кэша `isolated_numba_cache`)
- [ ] Документация `INSTALL.md` секция HIT FACTORY, `README.md` бейдж

---

## 5. Бесплатный стек (ни рубля)

| Компонент | Зависимость | Где в коде | Платно? |
|---|---|---|---|
| Python 3.10+ | `pyproject.toml` | — | нет |
| numpy, scipy, soundfile, librosa, pyloudnorm, pedalboard | `requirements.txt` | beat, mix, mastering | нет |
| CC0 сэмплы 808+BOOCHI44 | `data/samples/manifest.json` | `modules/beat/samples` | нет (CC0) |
| Шаблонный текст `punchlines.py` + `lyric_vault/slang.txt` | встроено | `modules/lyrics` | нет |
| pyttsx3 / gtts fallback | `requirements.txt` | `app/core/stages/vocal` | нет (локально/бесплатный API) |
| anti_neuro (numpy) | `modules/anti_neuro*.py` | vocal/track polish | нет |
| hit_scorer (librosa) | `modules/hit_scorer` | оценка | нет |
| trend_scout offline fallback | `agents/trend_scout.FALLBACK_2026` | themes | нет |
| Ollama local LLM (опц.) | `modules/llm/ollama_adaptive` | lyrics | нет (локально) |
| DuckDuckGo HTML / Reddit JSON (опц.) | `urllib.request` | trend_scout live | нет (без ключа) |

Тяжёлые модели (ACE-Step, MusicGen, RVC, Demucs, SDXL, CLAP, faster-whisper) — **опциональны** и не нужны для хита. Factory честно ставит `BLOCKED` если их нет, но трек всё равно собирается.

---

## 6. Как это «как человек»

1. **Не ровная сетка**: каждый удар сдвинут на −9…+9мс по таблице `PART_FEEL_MS` (kick −1.2…+1.4, hat −3…+2.4, snare +2…+7) + swing 50% step_ms на нечётных шагах + jitter ±0.5мс каждые 4 такта.
2. **Не ровная громкость**: velocity 0.88–1.12 × accent 1.09 на сильных долях (0,4,8,12) + ghost 0.28 ×0.85–1.15 + случайный недобор 6% ×0.72.
3. **Не один сэмпл**: round-robin `variant_index` по 3–4 вариантам каждого инструмента, чередование snare/clap по тактам.
4. **Не идеальный вокал**: микропровалы 40мс −6…−10дБ 3% шагов, детюн ±4 cents блоками с hanning кроссфейдом, дыхания −18дБ в паузах между фразами (сохранение длины).
5. **Не пластиковый верх**: `de_plastic` срезает >15.5кГц наполовину, `consonant_boost` поднимает 3–10кГц только на атаках.
6. **Не копия куплета**: `entropy_boost` режет <120Гц во второй половине трека.
7. **Не мимо бита**: вокал кладётся на сетку с `vocal_offset_ms` + сохранением длины, sidechain качает низ под кик.

Метрика: если выключить `humanizer`, `hit_scorer novelty` и `structure_clarity` падают, `mix correlation` уходит за 0.9 (узкая стерео-история машины). С ним — в коридоре 0.6–0.85.

---

## 7. API

```python
from modules.hit_factory import HitFactory, quick_hit

# Один хит
hit = quick_hit(theme="лето, тачки, Стамбул", genre="drift_phonk", seed=42)
print(hit["hit_score"], hit["verdict"], hit["master_path"])

# Фабрика
factory = HitFactory(min_score=68, evolve=True, max_attempts=3, duration_sec=120)
batch = factory.make_batch(count=5, genre="trap")
for h in batch:
    print(h["project_id"], h["hit_score"], h["verdict"])

# Эволюция вручную
from modules.hit_factory.evolver import mutate
next_recipe = mutate(prev_recipe, hit_report)
```

CLI:
```bash
python hitmaker.py --help
python hitmaker.py --count 10 --genre jersey_club --evolve --min-score 68 --duration 90
python main.py --hit-factory --count 5 --genre phonk --theme "ночь, неон, флекс"
```

---

## 8. Честность и ограничения (важно)

- **Не гарантия чарта**: `hit_score` — эвристика из 12 DSP-метрик, а не предсказатель Billboard. `chart_ready` (≥82) значит «похож на хит по структуре/громкости/повторяемости», а не «завтра в топе».
- **Scaffold ≠ вокал**: если нет `pyttsx3`/`Silero`/`XTTS`, вокал — формантный `rap_scaffold_numpy_v22` (честно помечается `synthetic: true, blocked: true`). Это placeholder для прогона микса, не пение человека. Для «как человек» нужен реальный TTS или своя запись (`own_vocal_wav`).
- **Детерминизм**: одинаковый `seed` + `genre` + `BPM` + `theme` → побайтово тот же `beat.wav` (проверяется SHA-256), но не гарантирует одинаковый `hit_score` если менялся `sample bank`.
- **Windows/GPU не проверены в этом коммите**: Linux CPU прогоны `smoke_audio 6/6`, `smoke_god 8/8`. Требуются `PROJECT_STATE.md` проверки на Win11 + микрофон + GPU.
- **ISRC/LRC**: не генерируются фейково (USER_SUPPLIED_UNVERIFIED только если введён вручную). `output/hits` не является релизом в дистрибуцию.

---

## 9. Дальше

См. раздел 4 Фаза 2–5. Ближайший шаг — запустить `python hitmaker.py --count 5 --evolve` на чистой машине, собрать `output/hits/benchmark.json` и подтюнить веса жанров по реальным `hit_score`.


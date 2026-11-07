# Полный разбор репозитория ZS-MUSIC-MAKER

> Ревизия: `41.0.0-alpha.16`, единственный коммит в истории (`638f7fe`, squash PR #8).
> Дата разбора: 2026-11-06. Ветка разбора: `arena/94173bba-zs-music-maker`.
> Метод: чтение всех файлов + статический анализ AST + прогон гейтов, тестов и реального
> пайплайна в Linux-песочнице (Python 3.11, CPU, без GPU).
> Приложение: полный файловый инвентарь (436 файлов, 54 735 строк) — [`docs/PROJECT_INVENTORY.md`](docs/PROJECT_INVENTORY.md).

---

## 1. Вердикт коротко

**Это не «прототип-обёртка», а большая инженерная система с редкой для таких проектов
культурой честности** — но с несколькими настоящими функциональными дырами, которые
маскируются этой же культурой («стадия OK, а внутри пусто»).

Что действительно хорошо:

- Пайплайн из 15 стадий с единым контрактом `StageResult` / `StageStatus` и **одним**
  местом подсчёта вердикта (`app/pipeline/stage.py:summarize`). Нет «почти ок».
- Fallback'и почти всегда помечены (`fallback_used`, `synthetic`, `blocked`, `engine`,
  `reason`), а `tools/audit_honesty.py` + `tools/fallback_audit.py` статически это стерегут.
- Целостность входов и пересборки сделана серьёзно: SHA-256 на входы и микс, отказ от
  symlink/`..`/чужого проекта, копирование через `tempfile`+`os.replace` с повторной проверкой
  (`app/core/revision.py`, `app/core/input_integrity.py`, `app/core/project_inputs.py`).
- Безопасность: **ноль** `shell=True`, `eval`, `pickle.load`, `os.system`; все `subprocess`
  с list-argv. Секреты — Fernet с PBKDF2-200k. Сеть по умолчанию выключена и это
  закреплено тестами (`tests/test_offline_network_policy.py`).
- Измеряемое качество звука: `modules/dsp/metrics.py` как единственный источник LUFS/true-peak,
  8 стендов мастеринга параллельно с побитовой идентичностью (`modules/mastering/stands.py`),
  hit-scorer из 12 взвешенных метрик.

Что требует немедленного внимания (детали в §5):

| # | Проблема | Где |
|---|---|---|
| 1 | Онлайн-поиск сэмплов **не работает вообще**: нет `import re/json/os` | `agents/sample_hunter/web.py` |
| 2 | Стадия `_stage_arrangement` — **пустышка**, всегда `{"sections": []}`, но статус `OK` | `app/core/stages/prep.py:161` |
| 3 | Рендер-очередь в автономном режиме **падает** (несуществующие `Orchestrator`, `probe_hw`) | `modules/render_queue.py:191` |
| 4 | Видео-fallback **всегда** падает (нет `_read_wav_mono`, `wave`, `struct`) | `modules/video_edit/render.py:186` |
| 5 | Режим качества `fast/quality/max` **никуда не доезжает** | `app/core/recipe.py:121` |
| 6 | `n_verses` **игнорируется** шаблонным fallback'ом текста | `app/core/stages/lyrics.py:275` |

---

## 2. Как проверялось

Песочница: Linux x86-64, 2 vCPU, Python 3.11.2. Первый прогон был «чистым» (без сторонних
пакетов), затем поставлен минимальный аудио-стек (numpy/scipy/soundfile/librosa/pyloudnorm/
pedalboard/Pillow/pytest) — это позволило прогнать реальные гейты, а не только статику.
PySide6 импортируется, но окно не поднимается (нет `libGL`), поэтому GUI проверялся
статически + тестами на Qt-стабах.

Запущено и получено:

| Проверка | Результат |
|---|---|
| `compileall` | 0 ошибок |
| `pytest tests/` | **840 passed, 2 skipped** (842 собрано) — 3 мин 53 с |
| покрытие (`--cov`) | **61 %** (21 134 инструкции, 8 179 непокрыто) |
| `tools/ast_dead_imports.py` | CLEAN |
| `tools/audit_honesty.py` | CLEAN (268 файлов) |
| `tools/fallback_audit.py` | 281 файл, 0 red flags (exit 0) |
| `tools/gitignore_guard.py` | CLEAN |
| `tools/samples_audit.py` | 32 CC0 one-shot, OK |
| `tools/audit_data_inventory.py` | 105 файлов: managed 105, unknown 0 |
| `tools/genre_validator.py` | 50/50 пресетов, 119 runtime-жанров, PASS |
| `python -m tools.readiness` | 60 % без зависимостей → **65 %** с зависимостями (caps: микрофон 80, тяжёлые движки 65) |
| `tools/smoke_audio.py` | **6/6 PASS** (LUFS −14.0, true-peak −1.06 dBTP) |
| `tools/smoke_god.py` | **8/8 PASS** (120 с, peak −2.21 dB, 8 стендов) |
| `python main.py --e2e` | PARTIAL, 15/15 стадий, 8/8 мастеров, 9 файлов релиза |
| `--run --only master` (dry-run) | PASS, 50 % |
| `--run --seed 42` (полный, 20 с) | PARTIAL 87 %, 4 BLOCKED, 1 FALLBACK — 73 с |

Главный вывод по методологии: **проект проходит собственные гейты честно**, но сами гейты
покрывают не всё — часть дефектов ниже живёт именно в местах, куда ни один гейт не смотрит.

---

## 3. Карта системы

### 3.1 Слои

```
main.py (138) ── app/cli/parser.py (31 флаг) ── app/cli/{commands,pipeline,gui,probes,dossier}.py
                                                      │
              ┌───────────────────────────────────────┼──────────────────────────────┐
              │                                       │                              │
  app/core/orchestrator.py (400)          orchestrator_ai.py (129)      orchestrator_god.py (99)
  run_full_pipeline — 15 стадий           SequentialAIRunner            = тот же DAG, 120 с
              │                                       │
   app/core/stages/*.py (12 файлов)        app/core/ai/stages_*.py (5 файлов)
              │                                       │
   modules/{beat,mix,mastering,lyrics,release,vocal_fx,dsp,hit_scorer,…}
              │
   app/audio/samples.py → data/samples/manifest.json (32 сэмпла)
```

Три входа (classic / AI / God) сведены к одному DAG — это правильное решение, и в
`orchestrator_god.py` прямо написано, почему: раньше два пайплайна расходились по качеству.

### 3.2 Поток данных (classic)

| # | Стадия | Что делает | Fallback |
|---|---|---|---|
| 1 | `_stage_analyze` | BPM/лад/агрессия из референсов (librosa) | жанровый дефолт (`genre_default`) |
| 2 | `_stage_groove` | грув из референса | 16-шаговый паттерн жанра |
| 3 | `_stage_arrangement` | «план аранжировки» | **пустой план** (см. §5.2) |
| 4 | `_stage_beat` | `beat_constructor.construct_beat` → сэмпловый банк + синтез | `_synth_beat` (полноценный synth-бит) |
| 5 | `_stage_texture` | MusicGen | synth-скаффолд (`synthetic=True`) |
| 6 | `_stage_lyrics` | `lyrics_llm` → LLMRouter (OpenRouter→Grok→Gemini→Ollama) | локальный шаблон |
| 7–9 | vocal: `voice_synth` → `rvc` → `vocal_fx` | своя запись приоритетна; TTS/RVC — fallback | BLOCKED с причиной |
| 10 | `_stage_mix_and_sidechain` | `modules.mix.bus`: gain staging, дакинг <120 Гц, ширина, гейты | — |
| 11 | `_stage_mastering` | 8 стендов, сходимость по LUFS, crest | честная копия |
| 12 | `_stage_polish` | anti-neuro (`polish_track`) | цепочка из 3 кандидатов |
| 13 | `_stage_stems` | Demucs | BLOCKED |
| 14 | `_stage_hit_score` | 12 метрик, веса | частичные метрики |
| 15 | `_stage_release_pack` | masters/stems/metadata/manifest(SHA-256)/ZIP | минимальный пакет |

Вердикты: `PASS` → `PASS_WITH_FALLBACK` → `PASS_BLOCKED` → `BLOCKED_SIMULATION` → `PARTIAL`,
причём при симуляции процент **ограничен 60** — «зелёный отчёт на заглушках» получить нельзя.
Отдельно от вердикта живут quality-gates (`_quality_gate_failures`): записанный WAV ещё не
значит пройденные гейты, и падение гейта понижает `PASS*` до `PARTIAL`.

### 3.3 Объём

| Каталог | Файлов | Строк |
|---|---:|---:|
| `modules/` | 145 | 22 315 |
| `tests/` | 149 | 13 891 |
| `app/` | 93 | 13 266 |
| `tools/` | 25 | 3 139 |
| `agents/` | 9 | 776 |
| `updater/` | 9 | 719 |
| `ui/`, `config/`, корень | 6 | 629 |
| **итого** | **436** | **54 735** |

Данные: `config/genres_100.json` (120 записей → 118 уникальных + `drift_phonk` = **119**),
`data/genre_presets/*.json` (ровно 50), `data/samples/` (32 CC0, 2.3 МБ),
`data/prompts/`, `data/artist_dossier/`.

---

## 4. Сильные стороны (подтверждено измерениями)

1. **Единый контракт стадий.** `app/pipeline/stage.py` — 207 строк, из них `summarize()`
   единственное место, где считается вердикт и процент. `StageResult.ok` намеренно
   отделён от `succeeded`, чтобы BLOCKED не притворялся успехом.
2. **Мастеринг.** 8 стендов считаются в пуле `min(cpu, 4)`, но результат **бит-в-бит**
   детерминирован; `stands.py` перечитывает `master_one` из пакета, чтобы honour-ить
   monkeypatch в тестах — редкая аккуратность.
3. **Детерминизм по seed — проверен, а не заявлен.** Два прогона с `seed=7`
   (`--only beat,texture`) дали идентичные SHA-256 для `beat.wav` и `texture_scaffold.wav`.
   `_apply_seed` фиксирует `random` + `numpy.random` (`pipeline_runtime.py:76`), а внутри
   `modules/beat/*` используется собственный `default_rng(seed)`.
   *Оговорка:* в `run_ai_pipeline` `_apply_seed` **не вызывается** — AI-путь невоспроизводим.
4. **Целостность.** `revision.py` требует полный не-resume рендер, валидный вердикт, все
   строки `REUSED_FOR_MASTER`, совпадение SHA-256 и размера микса, запрещает symlink/`..`/
   чужой проект, копирует через tempfile+`os.replace` и **перепроверяет** байты после копирования.
5. **Офлайн по умолчанию.** `freesound_client.online_enabled()` требует явного
   `allow_online=True` **или** `data/settings.json` с `{"network": {"online": true}}`
   (строго `is True`); апдейтер так же. Это закреплено 4 тестами.
6. **Отсутствие опасных API.** Проверено grep'ом по всему prod-коду: 0 `shell=True`,
   0 `eval`, 0 `pickle.load`, 0 `os.system`. Один настоящий bare `except:` — и тот в
   тексте докстринга `tools/audit_honesty.py`.
7. **Документация ограничений.** README/INSTALL/PROJECT_STATE честно перечисляют, что не
   проверено (Windows, реальный микрофон, GPU, пение). Это редкость и это надо сохранять.

---

## 5. Дефекты по severity

### P0 — ломает заявленную функцию

#### 5.1 Онлайн-поиск сэмплов не работает: отсутствуют импорты
`agents/sample_hunter/web.py` использует `re`, `json`, `os`, но импортирует только
`quote_plus` и `requests` из конфига (строки 10–14):

- `search_freesound_web` → `re.findall` (стр. 42) → `NameError`
- `search_wikimedia` → `json.loads` (стр. 69) → `NameError`
- `search_archive_org` → `json.loads` (стр. 107) → `NameError`
- `search_pixabay` → `os.environ` (стр. 131) → `NameError`

Проверено исполнением: с подменённым `_http_get` все четыре функции падают с `NameError`.
Снаружи это **не видно**: `hunter.search_online()` оборачивает каждый источник в
`except Exception: continue`, поэтому GUI показывает «online: 0» вместо ошибки.
Пользователь жмёт «найти сэмплы» и получает «ничего не найдено» — при этом сеть,
возможно, работала.

Дополнительно: `agents/sample_hunter/config.py:24` и `:27` дублируют `AUDIO_EXT` один и тот же.

#### 5.2 `_stage_arrangement` — стадия-пустышка со статусом OK
`app/core/stages/prep.py:161`:

```python
plan = ae.plan(analysis) if hasattr(ae, "plan") else {"sections": []}
```

У `modules/arrangement_engine` **нет** `plan` (есть `build_arrangement(style_vector,
total_seconds, seed, genre_override, hit_targets, variant)`), поэтому ветка `else`
срабатывает всегда. Результат — `{"ok": True, "plan": {"sections": []}}`, то есть стадия
попадает в отчёт как **OK**, а не BLOCKED/FALLBACK. Подтверждено на живом прогоне:
в `report.json` стадия `OK`, `plan.sections == []`.

Последствия:
- Третья из пятнадцати стадий не делает ничего, но занимает место в `percent`.
- `modules/arrangement_engine.build_arrangement` (341 строка: секции, `tiktok_hook`, `fx`,
  riser'ы) **не вызывается из продакшена вообще** — только из `tests/test_arrangement_engine_plan.py`.
  То есть годный код есть, а подключён он только к тесту.
- `build_arrangement_plan()` в `recipe.py:197` лишь дописывает `duration_sec`, `aggression`,
  `n_verses` в пустой план.
- `_stage_beat` секции плана **не читает**: он строит структуру сам
  (`app/core/stages/beat.py:152` — жёсткий список `intro/verse/pre/chorus/…`, а
  `beat_constructor` берёт структуру из `modules/beat/dramaturgy.plan_sections`).
  Итог: `n_verses` доезжает до драматургии бита (`dramaturgy.py:160`) и до промпта текста,
  но план аранжировки на музыку не влияет.

**Это главный архитектурный дефект**: стадия есть, код есть, связи нет, а отчёт зелёный.

### P1 — функция заявлена, но на практике отказывает

#### 5.3 Рендер-очередь: несуществующие импорты
`modules/render_queue.py:191-193` (автономный режим, когда оркестратор не передан):

```python
from app.core.orchestrator import Orchestrator     # такого имени нет — есть run_full_pipeline
from app.hw_probe import probe_hw                  # есть только probe
from app.core.logger import make_logger            # есть make_logger(name="…")
```

`ImportError` выбрасывается внутри `_process`, попадает в общий `except` и превращается в
`item.status = "error"` — очередь не рендерит ни один трек, если её создали «самостоятельно».

Смежное: `modules/rvc_trainer.py:194` делает `from modules.render_queue import enqueue`,
а модульного `enqueue` не существует (есть метод `RenderQueue.enqueue`, стр. 102). Ветка
`except` тихо уходит в `retrain_incremental(dry_run=True)`, то есть «ночное обучение»
всегда dry-run.

#### 5.4 Видео-fallback: три отсутствующих импорта
`modules/video_edit/render.py` в `_build_fallback` вызывает `_read_wav_mono` (стр. 186),
`wave.open` (190) и `struct.pack` (196). Ни `_read_wav_mono` (живёт в
`modules/video_edit/audio.py:16`), ни `wave`, ни `struct` в модуль не импортированы.
Проверено исполнением: `NameError: name '_read_wav_mono' is not defined` → функция
возвращает `backend='fallback_txt'` и файл `*_build_manually.txt`. Честно, но
заявленный «честный fallback WAV» не работает никогда.

#### 5.5 `HAS_LIBROSA` всегда `True` (мёртвый флаг)
`modules/voice_vault.py:33`:

```python
try:
    HAS_LIBROSA = True      # нет import librosa
except Exception:
    HAS_LIBROSA = False
```

AST-скан по всему репозиторию: это **единственный** такой случай (в `hit_scorer/audio.py`
и `reference_ingest.py` импорт есть). Хорошая новость: сам флаг в `voice_vault` нигде не
читается, `librosa` в файле не упоминается ни разу — то есть это не рабочий баг, а
мёртвый код, вводящий в заблуждение. Лечится удалением пяти строк.

#### 5.6 `quality_mode` (Fast/Quality/Max) ни на что не влияет
`recipe.py:121` пишет `quality_profile = {rvc_epochs, mastering_iterations}`, и **ни один
модуль его не читает** (проверено grep'ом по `app/ modules/ tests/`). `quality_mode`
используется только как информационное поле в `report.json` и в `project_snapshot`.

Единственное место, где режим качества реально существует, — MusicGen-текстуры
(`app/core/musicgen_texture.py:choose_size`), но стадия вызывает
`generate_texture(...)` **без** `quality_mode` (дефолт `"quality"`), а
`generate_texture_for_vibe` вообще жёстко передаёт `quality_mode="quality"`.

Итог: пользователь переключает Fast/Quality/Max в визарде — на результат это не влияет
(ни RVC-эпохи, ни число итераций мастеринга). Это ровно тот класс «фейкового успеха»,
против которого написан `audit_honesty`, просто он не ищет неиспользуемые поля рецепта.

#### 5.7 `n_verses` не доезжает до шаблонного fallback
- В AI-промпт — доезжает (`lyrics.py:207`, `generate_lyrics_ai(..., n_verses=)`).
- В промпт LLMRouter — доезжает (`lyrics.py:223`, `verses = clamp(1..4)`).
- В шаблонный fallback — **нет**: `_fallback_lyrics(theme, genre)` (`lyrics.py:164`,
  вызов на стр. 275) принимает только тему и жанр и всегда отдаёт фиксированную
  структуру `verse1/chorus/verse2` из `_LYRICS_TEMPLATES`.

Поскольку в песочнице LLM недоступен, это дефолтный путь: пользователь просит 4 куплета,
получает 2. Стадия при этом честно помечена FALLBACK — но выбор пользователя потерян молча.

#### 5.8 «Три варианта» на экране результата — это не три варианта
`app/gui/wizard/steps_run.py:369` `three_variants()` кладёт в рецепт `variant = 1..3`,
но **`variant` не читается нигде** в продакшене (grep: только `project_snapshot` и
`registry`-не related). Реально меняется лишь `aggression = 0.4/0.6/0.8`.
Разные варианты будут различаться громкостью транзиентов, а не аранжировкой.

### P2 — тихая деградация и несоответствия

#### 5.9 `trend_scout` ищет несуществующий модуль
`agents/trend_scout.py:178`: `from modules.lyrics_gen import load_slang_dictionary`.
Модуля `modules/lyrics_gen` в репозитории нет (есть пакет `modules/lyrics`), функция
`load_slang_dictionary` не существует нигде. Ветка всегда уходит в `diagnostics` как
`failed`. Практически: локальный сленг в тренды не попадает никогда; работает только
DuckDuckGo (если есть сеть) и встроенный fallback-список.

#### 5.10 ID3-теги заявлены в UI и health, но не пишутся
`mutagen` есть в `requirements.txt`, в `modules/health.py` (как «quality» с советом
«ID3-теги не пропишутся»), в i18n («Artist name (ID3 tags)») и в онбординге
(«Всё с твоим именем в ID3-тегах»). Но **ни один модуль `mutagen` не импортирует**:
релиз пишет `metadata.json` + `metadata.csv` + `manifest.json` и копирует WAV **без тегов**
(`modules/release/export.py`). Пользователю обещано то, чего нет; при этом честный
`metadata.csv` уже покрывает потребность дистрибьютора.

#### 5.11 Онлайн-поиск сэмплов включён по умолчанию — в обход политики «офлайн»
`agents/sample_hunter/hunter.py:62`: `hunt(..., allow_online: bool = True)`.
В GUI чекбокс «онлайн» тоже выставлен в `setChecked(True)` (`steps_tuning.py:78`).
То есть один клик по «искать сэмплы» уходит в сеть, хотя `freesound_client` и `updater`
требуют явного opt-in. Политика сети в проекте есть, но **несогласована** между тремя
подсистемами (freesound_client / updater / sample_hunter), и тест
`test_offline_network_policy.py` покрывает только первые две.

Заодно: `hunt()` не возвращает `total`, хотя `unified_search()` возвращает —
`KeyError: 'total'` при попытке прочитать его у `hunt()` (проверено).

#### 5.12 Веса моделей могут скачиваться при первом использовании
README (`стр. 66-67`) утверждает: «Во время обработки веса автоматически не скачиваются».
Фактически `local_files_only=True` есть только у llama-cpp (`registry.py:316`) и
faster-whisper. А вот:

- `MusicGen.get_pretrained(repo)` — `registry.py:263`, `musicgen_texture.py:58`
- `get_model("htdemucs")` — `registry.py:291`
- `ClapModel.from_pretrained(...)` — `registry.py:323-324`
- `DiffusionPipeline.from_pretrained(...)` — `registry.py:343`
- XTTS `TTS(model_name=...)` — `registry.py:272`

При наличии пакета и отсутствии локальных весов эти вызовы пойдут в Hugging Face.
Это не «фейк», но расхождение с обещанием и с духом офлайн-политики.

#### 5.13 Апдейтер: пути пользовательских данных не совпадают с реальными
`updater/userdata.py:22` `USER_PRESERVED` содержит `"secrets.enc"` и `"settings.json"`
в корне программы, а фактически они лежат в `data/` (`modules/llm/secrets.py:27`,
`modules/freesound_client.py:41`). Значит при обновлении LLM-ключи и настройки сети
попадают под «очистку каталога программы». `data/tutorial_settings.json`,
`voice_vault`, `lyric_vault`, `output` — перечислены верно.

#### 5.14 Апдейтер: Zip Slip
`updater/install.py:51` и `:169` используют `zipfile.extractall(...)` без проверки
имён на `..`/абсолютные пути. Проверено: на Python 3.11 `extractall` **нормализует**
`../../escaped.txt` внутрь целевой папки, но абсолютные имена сохраняются как
относительные — то есть on-CPython-3.11 это не эксплойт, а зависимость от поведения
stdlib. `verify_zip` проверяет только «есть ли `main.py`/`version.json`/`modules/*.py`»
и диапазон размера 1 КБ…5 ГБ, но не список путей. Правильная защита — одна функция
`_safe_extract` с `Path(target, name).resolve().is_relative_to(target)`.

#### 5.15 Дубли и мёртвые реализации
- Sidechain: `modules/sidechain.py` (290 строк, «настоящий sidechain») **не используется** —
  весь дакинг живёт в `modules/mix/ducking.py`. Два описания одного и того же.
- `app/core/pipeline_core.py` (158 строк, «заменяет монструозный orchestrator.py») — не
  импортируется ниоткуда, кроме самого себя; `tools/readiness` числит его в PLANNED.
- Три входа в генерацию текста: `modules/lyrics/generate.py` (используется),
  `modules/lyrics/ai.py` (используется), `modules/lyrics/author.py::generate_lyrics_v8`
  (только тесты).
- `modules/mastering_chain.py` — legacy-адаптер «на случай старых вызовов», живых
  вызовов нет (кроме `tools/smoke_god.py`).

#### 5.16 ~4 800 строк недостижимого продакшн-кода
BFS по графу импортов от `main.py`/`install.py`/`app.cli`/`app.gui`/`tools`/`updater`/`ui`
(287 prod-модулей; 34 недостижимы):

```
app/core/pipeline_core.py      app/plugins/{base,advanced}.py
modules/ai_arranger.py         modules/essentia_analyzer.py    modules/track_templates.py
modules/chanson_engine.py      modules/remix.py                modules/phonk_engine.py
modules/female_backing.py      modules/expert_mode.py          modules/kpi_monitor.py
modules/lyric_vault.py         modules/auto_qa.py              modules/hw_directml.py
modules/freesound_client.py    modules/tiktok_edit.py          modules/reference_ingest.py
modules/sidechain.py           modules/karaoke_engine.py       modules/onboarding.py
modules/phoneme_coverage.py    modules/{video_edit/*}          modules/*/__main__.py
```

Важная деталь: `tools/readiness` считает `REAL_PASS` по формуле «файл парсится **и** на
него есть статическая ссылка», причём `production_refs` включает упоминания в самом
`tools/` и в комментариях. Поэтому 284/287 = «REAL_PASS», а `PLANNED` всего 3
(`ai_arranger`, `essentia_analyzer`, `track_templates`) — при том что `expert_mode` (324 строки),
`kpi_monitor` (397), `lyric_vault` (252), `tiktok_edit` (267) тоже не вызываются из
пользовательских путей. **Индикатор готовности переоценивает реальную связность.**

### P3 — гигиена, документация, мелочи

| Проблема | Факт |
|---|---|
| Правило «функция ≤ 60 строк» | 27 функций ≥ 90 строк; худшие: `orchestrator.run_full_pipeline` **315**, `stages/beat._synth_beat` 259, `beat/constructor.build_track` 243, `theme.qss` 190, `beat/arrangement._build_section` 171 |
| Правило «файл ≤ 400 строк» | в проде соблюдено (`test_code_hygiene.py` держит), в тестах — нет: `test_ai_quality.py` 812 |
| Широкие `except Exception` | 462 вхождения; `pass`-глотание — 6 (`updater/{archive×2,install×2,userdata}`, один в тесте) |
| `docs/ARCHITECTURE.md:18` | «15 стадий, **339 строк**» — в файле 400 |
| `docs/ARCHITECTURE.md:26` | «wizard (**9 шагов**)» — шагов 5 (в README и `window.py` — верно) |
| `docs/ARCHITECTURE.md:178` | «**526 тестов**» — tests-функций 733, собирается 842 |
| `docs/ARCHITECTURE.md:121`, `WORKFLOW.md:30` | `app/ai/quality.py` — это **пакет** `app/ai/quality/` |
| `ARCHITECTURE.md:130,132`, `WORKFLOW.md:20` | `data/genres/` и `data/schema/` **не существуют**; жанры берутся из `config/genres_100.json` + хардкод `drift_phonk` в `StyleRegistry._load_defaults` |
| `PROJECT_STATE.md:29` | «841 passed» — сейчас 840 (и `:254` «736 passed» — третья цифра в том же файле) |
| `build.yml:36` | собирает `--onefile` **в обход** `packaging/zsmm.spec`, хотя spec по умолчанию onedir и аргументирует это (медленный старт, антивирус). Два источника правды для упаковки |
| `packaging/zsmm.spec:3` | докстринг говорит «(Windows 11, onefile)», а внутри — обоснование onedir |
| `tools/quality_gate.sh` | требует `mypy`/`pylint`, которых нет ни в одном requirements; печатает «10/10 SCORE» |
| `requirements.txt` неиспользуемое | `matplotlib`, `audioread`, `click`, `omegaconf`, `plyer`, `mingus`, `tqdm`, `mutagen` (0 импортов каждое) |
| `agents/sample_hunter/config.py` | `AUDIO_EXT` объявлен дважды (стр. 24 и 27) |
| `config/genres_100.json` | 120 записей → 118 уникальных: `trap` и `grime` дублируются в двух категориях |
| `app/core/i18n.py` | ru/en по 166 ключей, расхождений нет — здесь всё чисто |

---

## 6. Детерминизм: уточнение

Ранее подозрение было на `np.random.randn` в `stages/beat.py` и `stages/texture.py`.
**Проверено измерением — воспроизводимость есть**: `_apply_seed` вызывает
`np.random.seed(seed)`, поэтому глобальный поток тоже фиксируется; два прогона с
`seed=7` дали одинаковые SHA-256.

Остаются два реальных риска:

1. **AI-путь** (`run_ai_pipeline`) `_apply_seed` не вызывает и `seed` из `ws` не использует —
   воспроизводимость там не гарантирована вообще.
2. Глобальный RNG — общий ресурс: любая сторонняя библиотека, дернувшая `np.random`,
   сдвинет поток. В `modules/beat/*` это уже исправлено (`default_rng`), в стадиях — нет.
   Рекомендация: передать `rng` в `_synth_beat`/`_texture_scaffold` явно.

---

## 7. Тесты и CI

**Что есть (и это выше среднего):**
- 149 файлов, 733 `test_`-функции, 842 собранных теста, 61 % покрытия инструкций.
- Сильные домены: `ai` (93 теста), `beat` (45), `mastering` (45), `voice` (32),
  `pipeline` (29), `sample` (23), `mix` (22), `dsp` (21, включая property-based на hypothesis).
- Отдельно проверяются именно «нечестные» вещи: `test_offline_network_policy.py`
  (сеть выключена, `is True`-строгость), `test_pipeline_determinism_and_partial_runs.py`
  (seed → одинаковый SHA-256), `test_master_revision.py` (577 строк проверок целостности),
  `test_user_vocal_safety.py`, `test_kpi_telemetry_privacy.py`.
- `test_code_hygiene.py` держит «файл ≤ 400 строк» и «нет `*_vN`-модулей» через `git ls-files`.

**Где дыры (ровно там, где дефекты §5):**
- нет ни одного теста на `agents/sample_hunter/web.py` → P0 5.1 прошёл незамеченным;
- нет теста, проверяющего, что `_stage_arrangement` возвращает **непустой** план →
  P 5.2 живёт при зелёном CI;
- `modules/render_queue.py`, `modules/video_edit/render.py`, `modules/expert_mode.py`,
  `modules/track_templates.py`, `modules/ai_arranger.py`, `modules/essentia_analyzer.py`,
  `modules/tiktok_edit.py` — **0 %** покрытия;
- 0 % также у `app/gui/wizard/{steps_brief,steps_material,steps_tuning,ui,dialogs}.py`
  (тестируются через Qt-стабы выборочно), `app/core/license_manager.py`,
  `app/core/numba_cache.py` (при том что он есть), `modules/presets.py`;
- `updater/archive.py` 15 %, `updater/install.py` 42 %, `updater/userdata.py` 38 % —
  самый рискованный код (удаляет каталог программы) покрыт слабее всего;
- нет теста на zip-slip и на сохранность `data/secrets.enc`.

**CI** (`.github/workflows/ci.yml`): три джоба — `test` (ubuntu: pytest + smoke_audio +
smoke_god + fallback_audit + CLI-санити), `audit` (compileall + ast_dead_imports + pytest),
`windows` (то же на windows-latest, timeout 45 мин). Дублирование прогонов между джобами
присутствует (pytest дважды на ubuntu), но по существу CI правильный: целевая платформа
в матрице. `build.yml` собирает EXE и делает smoke `--version` (не `continue-on-error`).

---

## 8. Документация vs реальность

| Документ утверждает | Факт |
|---|---|
| «526 тестов» (ARCHITECTURE:178) | 842 собрано / 840 проходит |
| «9 шагов» визарда (ARCHITECTURE:26) | 5 шагов |
| «339 строк» оркестратора | 400 |
| `app/ai/quality.py` | пакет `app/ai/quality/` |
| `data/genres/*.json`, `data/schema/` | каталогов нет |
| «веса автоматически не скачиваются» (README:66) | MusicGen/Demucs/CLAP/SDXL/XTTS пойдут в HF |
| «имя артиста в ID3-тегах» (онбординг, i18n, health) | теги не пишутся, mutagen не используется |
| «841 passed» (PROJECT_STATE:29) | 840 |
| «Готовность 65 %» (PROJECT_STATE) | 65 % с зависимостями, 60 % без; индикатор переоценивает связность (§5.16) |

Плюс к этому: `README`, `INSTALL`, `ROADMAP`, `BLIND_LISTENING` — **точны и честны**
в части ограничений. Расхождения концентрируются в `ARCHITECTURE.md`, `WORKFLOW.md` и в
маркетинговых строках UI про ID3.

---

## 9. Что делать: приоритетный план

**P0 (часы, ломает пользовательский сценарий):**
1. `agents/sample_hunter/web.py`: добавить `import re`, `import json`, `import os`;
   в `hunter.search_online` **не глотать** `NameError`/`ImportError` — писать в
   `result["diagnostics"]`, как это уже сделано в `trend_scout`. Добавить тест на
   четыре парсера с фикстурным HTML/JSON (тестов нет вообще).
2. `app/core/stages/prep.py`: вызывать реальный API —
   `ae.build_arrangement(resolve_style_vector(recipe, analysis), total_seconds=…, seed=…, variant=…)`,
   либо, если это осознанно отложено, возвращать `{"ok": False, "blocked": True,
   "reason": "arrangement planner not wired"}`. Нынешнее `{"ok": True}` при пустом плане —
   ровно тот «ложный успех», который проект сам запрещает.

**P1 (день-два):**
3. `render_queue._process`: `from app.core.orchestrator import run_full_pipeline` (+ обёртка),
   `from app.hw_probe import probe`, `make_logger()` без аргумента; `rvc_trainer` — либо
   модульный `enqueue()`, либо `RenderQueue().enqueue(payload)`.
4. `video_edit/render.py`: `from modules.video_edit.audio import _read_wav_mono`,
   `import wave, struct`; тест на fallback с реальным WAV.
5. Связать `quality_mode`: прокинуть `recipe["quality_profile"]` в `generate_texture`,
   в число итераций мастеринга (`mastering/loudness._converge_loudness`) и в RVC-эпохи —
   или убрать переключатель из визарда. Полумеры здесь хуже удаления.
6. `_fallback_lyrics(theme, genre, n_verses)` — генерировать `verse1..verseN` по числу
   куплетов (шаблон уже словарный, расширяется тривиально).
7. `voice_vault.py:33` — удалить мёртвый `try/HAS_LIBROSA`.

**P2 (неделя):**
8. Определиться с `variant`: либо `build_arrangement(..., variant=)`/`plan_sections`,
   либо убрать кнопку «3 варианта» и честно назвать её «3 уровня агрессии».
9. `trend_scout`: заменить `modules.lyrics_gen` на существующий источник сленга
   (`lyric_vault/slang.txt` уже есть).
10. Решить судьбу ID3: либо `mutagen` в `release/export.py` (EasyID3 на копию мастера),
    либо убрать обещание из i18n/онбординга/health.
11. Апдейтер: `_safe_extract` с проверкой путей; `USER_PRESERVED` → `data/secrets.enc`,
    `data/settings.json`; тест «обновление не теряет секреты».
12. Единая политика сети: один хелпер `network_allowed()` для freesound/updater/sample_hunter,
    `hunt(allow_online=False)` по умолчанию, галочка в GUI — выключена.
13. Либо подключать, либо помечать `DEPRECATED` и выносить из `REAL_PASS`:
    `expert_mode`, `kpi_monitor`, `lyric_vault`, `tiktok_edit`, `video_edit`, `eidetic`-набор
    из §5.16. И поправить формулу `tools/readiness/inventory.py`: `production_refs` не
    должен считать самого себя и `tools/`.

**P3 (гигиена, по ходу):**
14. `ARCHITECTURE.md` — переписать цифры (5 шагов, 15 стадий, 400 строк, 842 теста, пакет
    `quality/`, реальные пути данных). Добавить в CI проверку «док не расходится с кодом»
    хотя бы для чисел, которые уже считает `tools/readiness`.
15. Разбить `run_full_pipeline` (315 строк) на `_run_music_block`, `_run_vocal_block`,
    `_run_finalize`; вынести `_synth_beat`/`build_track` частично — иначе правило
    «функция ≤ 60 строк» остаётся декларацией.
16. `build.yml` — собирать через `packaging/zsmm.spec`, а не дублировать флаги вручную.
17. Убрать из `requirements.txt` 8 неиспользуемых пакетов (уменьшит и вес установки,
    и поверхность обновлений).

---

## 10. Итоговая оценка

| Аспект | Оценка |
|---|---|
| Архитектура и связность ядра | 4/5 — единый DAG, чистые контракты, но одна стадия-пустышка и слой недостижимых модулей |
| Честность отчётов | 4/5 — сильная культура FALLBACK/BLOCKED, но `arrangement` и `quality_mode` — дыры |
| Аудио-качество (измеримое) | 4/5 — 6/6 smoke, LFUS/true-peak в норме, 8 стендов; субъективное качество не проверено |
| Безопасность | 4/5 — нет опасных API, хорошая работа с секретами и целостностью; минус zip-slip и `extractall` |
| Тесты | 4/5 — 840 зелёных, 61 % покрытия, отличные «нечестные» тесты; минус 0 % у updater/render_queue/video_edit |
| Документация | 3/5 — README/INSTALL/ROADMAP честные, ARCHITECTURE/WORKFLOW устарели, UI обещает ID3 |
| Готовность к Windows-релизу | 3/5 — CI собирает и курит EXE, но GUI, микрофон и модели на целевой машине не проверены (и проект это сам признаёт) |

**Общий вывод.** Проект заслуживает доверия больше, чем типичный «AI-музыкальный комбайн»:
он предпочитает сказать «BLOCKED», а не соврать. Но у этой дисциплины есть слепое пятно —
**стадия, которая «OK» и при этом ничего не делает**, и **настройка, которая сохраняется в
рецепт и нигде не читается**. Обе болезни лечатся не новым кодом, а двумя проверками в CI:
(1) стадия не может быть OK с пустым выходом; (2) каждое поле рецепта обязано иметь
читателя (AST-тест на «поле пишется, но нигде не читается»). Это ровно в духе того, что
автор уже сделал в `audit_honesty.py`.

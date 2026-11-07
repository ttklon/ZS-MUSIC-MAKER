# План доработок ZS Music Maker

> Основание: [`CODE_REVIEW.md`](../CODE_REVIEW.md) (ревизия `41.0.0-alpha.16`).
> Ветка: `arena/94173bba-zs-music-maker`.
> Принцип: каждая правка закрывается тестом, который **падал до неё**. Ни один пункт
> не считается сделанным без прогона гейтов из T23.

## 0.1 Решения владельца (зафиксировано)

| Вопрос | Решение |
|---|---|
| Объём | **Весь план Ф0–Ф5** |
| T18 / ID3 | **Реализовать теги** — EasyID3 на копию мастера в релизном пакете; оригинал не мутируется |
| Недостижимые модули | **Пометить `DEPRECATED`** — код остаётся, из индикатора готовности выходит с весом 0.25 |
| T6 / влияние плана на бит | «Как лучше» → **влияет, но под флагом** `ZSMM_ARRANGEMENT_DRIVES_BEAT` (по умолчанию **вкл**), с контрольными SHA-256 до/после и тестом на дефолтный откат |

## 0.2 Состояние выполнения

| Пункт | Статус |
|---|---|
| T1–T3 (Ф0, сторожа) | ☐ |
| T4–T7 (Ф1, P0) | ☐ |
| T8–T13 (Ф2, P1) | ☐ |
| T14–T18 (Ф3, P2) | ☐ |
| T19–T22 (Ф4, docs/гигиена) | ☐ |
| T23 (Ф5, верификация) | ☐ |

Базовая линия перед правками (Linux, CPU, зависимости из `requirements.txt` минус
тяжёлые): **839 passed, 3 skipped**, покрытие 61 %, `smoke_audio` 6/6, `smoke_god` 8/8,
`--e2e` PARTIAL 15/15, `readiness` 65 %.

---

## 0. Правила работы

1. **Сначала тест, потом фикс.** Для каждого дефекта — сначала падающий тест,
   воспроизводящий баг (в отчёте они уже воспроизведены вручную).
2. **Честный отказ лучше ложного успеха.** Если функцию нельзя включить корректно —
   она возвращает `{"ok": False, "blocked": True, "reason": ...}`, а не пустой `ok=True`.
3. **Ничего не удаляем молча.** Мёртвый модуль либо подключается, либо помечается
   `DEPRECATED` с причиной и выпадает из индикатора готовности.
4. **Обратная совместимость публичных API.** Новые параметры — только keyword-only
   со значением по умолчанию; поведение при старых аргументах не меняется.
5. **Один коммит = один пункт плана**, сообщение `fix(<область>): <T-id> <суть>`.

---

## 1. Фазы и порядок

| Фаза | Содержание | Пункты | Зачем именно так |
|---|---|---|---|
| **Ф0** | Гейты-сторожа | T1–T3 | Чтобы правки Ф1–Ф2 нельзя было «потерять» регрессией |
| **Ф1** | P0: сломанный функционал | T4–T7 | Пользовательские пути не работают прямо сейчас |
| **Ф2** | P1: заявлено, но не работает | T8–T13 | Настройки визарда не влияют на результат |
| **Ф3** | P2: тихая деградация | T14–T18 | Безопасность, политика сети, правдивость метрик |
| **Ф4** | Документация и гигиена | T19–T22 | Устранить расхождения, закрепить авто-проверкой |
| **Ф5** | Финальная верификация | T23 | Полная матрица гейтов + отчёт |

Оценка: Ф0 — 1 сессия, Ф1 — 1, Ф2 — 2, Ф3 — 2, Ф4 — 1, Ф5 — 1.

---

## Ф0. Гейты-сторожа

### T1 — «Стадия не может быть OK с пустым выходом»
**Файлы:** `app/core/pipeline_runtime.py`, `tests/test_stage_contract_nonempty.py`

Добавить в `_quality_gate_failures()` проверку контракта: для стадий с объявленным
непустым выходом (`_stage_arrangement`, `_stage_beat`, `_stage_mix_and_sidechain`,
`_stage_mastering`, `_stage_release_pack`) пустой/отсутствующий ключ результата —
это **провал гейта** (вердикт понижается до `PARTIAL`), а не «OK».

**Приёмка:** тест с monkeypatch `_stage_arrangement → {"ok": True, "plan": {"sections": []}}`
даёт `quality_gate_failures != []` и вердикт `PARTIAL`. Сейчас даёт PASS.

### T2 — «Каждое поле рецепта имеет читателя»
**Файлы:** `tests/test_recipe_contract.py`, `app/core/recipe.py`

AST-тест: собирает ключи словаря `build_recipe()` и ищет их чтение в `app/`, `modules/`,
`agents/`, `tools/` вне `build_recipe`. Белый список — только `project_id` (пишется в
отчёт) с комментарием. На момент написания теста он должен **упасть** на
`quality_profile`.

**Приёмка:** после T11 и удаления `extra_prompt` — зелёный; при добавлении нового
«мёртвого» поля — красный.

### T3 — «Документация не врёт цифрами»
**Файлы:** `tests/test_docs_numbers.py`

Проверяет, что числа в `docs/ARCHITECTURE.md` совпадают с фактом: число стадий
(`len(STAGE_RECORDS)`), шагов визарда (5), строк `orchestrator.py`, число тестов
(собирается через `pytest --collect-only -q`), наличие путей из таблицы данных.

**Приёмка:** до T19 — красный (5 расхождений из отчёта), после — зелёный.

---

## Ф1. P0 — то, что не работает

### T4 — `agents/sample_hunter/web.py`: восстановить онлайн-поиск
**Файлы:** `agents/sample_hunter/web.py`, `tests/test_sample_hunter_web.py`

- добавить `import json`, `import os`, `import re`;
- убрать дубль `AUDIO_EXT` в `agents/sample_hunter/config.py`;
- `hunt()` — добавить ключ `total`, как в `unified_search()` (сейчас `KeyError`);
- `hunter.search_online()` — не глотать `NameError`/`ImportError`: складывать в
  `result["diagnostics"]` по образцу `trend_scout`.

**Тесты (новые, на фикстурах — без сети):** `monkeypatch _http_get` → HTML Freesound,
JSON Wikimedia/archive.org/Pixabay → 4 парсера возвращают записи; недоступный источник →
`diagnostics` с именем источника и текстом ошибки; лицензионный gate режет `NC/SA/unknown`.

**Приёмка:** `pytest tests/test_sample_hunter_web.py` зелёный; вручную —
`hunt("kick")` возвращает `total`, `diagnostics` пуст при рабочем источнике.

### T5 — `_stage_arrangement`: подключить реальный планировщик
**Файлы:** `app/core/stages/prep.py`, `app/core/recipe.py`,
`modules/arrangement_engine.py`, `tests/test_arrangement_wiring.py`

- адаптер `arrangement_style(style_vector) -> dict` в `recipe.py`:
  `target_bpm→bpm`, `key_root→key`, `target_mode→mode`, `genre→genre_hint`;
- `_stage_arrangement(style, total_seconds, seed, variant, genre)` →
  `build_arrangement(...)`; исключение → `{"ok": False, "blocked": True, "reason": ...}`
  (**никогда** не пустой `ok=True`);
- `build_arrangement_plan()` сохраняет `sections`, `tiktok_hook`, `total_sec` и
  домешивает `duration_sec`/`aggression`/`n_verses`;
- `build_arrangement` — убрать неявный `time.time()` из `random.Random(seed or time())`:
  при `seed=None` использовать фиксированный дефолт и помечать `seeded: false`
  (иначе план невоспроизводим).

**Тесты:** `seed=42` дважды → идентичные `sections`; `sections` непусты и
`sum(section["duration_sec"]) ≈ total_sec`; `tiktok_hook.end_sec - start_sec ≤ 25`;
исключение внутри движка → `BLOCKED`, вердикт не PASS.

**Приёмка:** в `report.json` стадия `_stage_arrangement` содержит ≥ 6 секций;
`T1`-гейт зелёный.

### T6 — План аранжировки влияет на бит (иначе T5 — декорация)
**Файлы:** `app/core/stages/beat.py`, `app/core/orchestrator.py`, `modules/beat/dramaturgy.py`,
`tests/test_arrangement_drives_beat.py`

**Решение владельца:** влияние включается, но управляется флагом
`ZSMM_ARRANGEMENT_DRIVES_BEAT` (по умолчанию `1` = вкл; `0` возвращает прежнее
поведение один-в-один — это аварийный выключатель, а не мёртвый код).

- `_stage_beat` считает `n_verses`/`n_choruses` по именам секций плана
  (`verse*`, `hook/chorus*`) и передаёт их в `construct_beat`;
- `n_choruses` прокинуть в `plan_sections` (сейчас хардкод `=2`);
- при отсутствии плана, при `ZSMM_ARRANGEMENT_DRIVES_BEAT=0` и при `BLOCKED`-плане —
  текущее поведение (`recipe["n_verses"]`, 2 припева).

**Контроль до правки (обязательно зафиксировать):** `seed=7`,
`{"genre":"drift_phonk","theme":"t","duration_sec":12}`, `only={"beat"}` →
SHA-256 `beat.wav` = `<записать здесь перед коммитом T6>`; после правки при флаге `0`
хэш обязан совпасть, при флаге `1` — может отличаться (это и есть фикс).

**Тесты:** план с 3 куплетами → в отчёте бита 3 секции `verse`; `=0` → прежняя
структура и прежний SHA-256; отсутствие плана → поведение как сегодня.


### T7 — Ночь/очередь: оживить `render_queue` и `rvc_trainer.schedule_night_run`
**Файлы:** `modules/render_queue.py`, `modules/rvc_trainer.py`,
`tests/test_render_queue_standalone.py`

- `from app.core.orchestrator import run_full_pipeline` (+ тонкая обёртка `_run(recipe)`),
  `from app.hw_probe import probe`, `make_logger()`;
- `schedule_night_run`: `from modules.render_queue import RenderQueue` →
  `RenderQueue().enqueue(payload)`; при недоступности — `dry_run=True` оставить, но
  пометить `"fallback": True, "reason": ...` (сейчас причина теряется);
- `_process` для `kind == "rvc_train_night"` — явный `BLOCKED` с причиной, а не общий `error`.

**Тесты:** очередь из 1 задачи с подменённым `run_full_pipeline` → `status == "done"`;
отсутствие оркестратора не приводит к `ImportError`; payload `rvc_train_night` → `blocked`.

---

## Ф2. P1 — заявлено, но не работает

### T8 — `video_edit`: починить fallback и точки входа
**Файлы:** `modules/video_edit/render.py`, `modules/video_edit/audio.py`,
`tests/test_video_edit_fallback.py`

- импортировать `wave`, `struct`, `_read_wav_mono` из `audio.py` (или вынести хелпер в `audio.py`);
- `_read_wav_mono` — вернуть `(list[float], sr)` и не падать на стерео/24-бит;
- при отсутствии `moviepy` — `backend="fallback_wav"` и реальный `*_HOOK.wav`.

**Тесты:** сгенерировать WAV → `_build_fallback` создаёт `_HOOK.wav`, длительность ±0.05 с,
`backend == "fallback_wav"`. Сейчас — `NameError`.

### T9 — `voice_vault`: убрать мёртвый флаг
**Файлы:** `modules/voice_vault.py`

Удалить `try/HAS_LIBROSA` (строки 33–36). Тест не нужен — достаточно `compileall`
и grep-проверки в `T2`-стиле: любой `HAS_*` без импорта в `try` валит новый тест
`tests/test_optional_flags.py` (AST-скан по всему прод-коду).

### T10 — `trend_scout`: источник локального сленга
**Файлы:** `agents/trend_scout.py`, `tests/test_trend_scout_slang.py`

Заменить `from modules.lyrics_gen import load_slang_dictionary` на чтение
`lyric_vault/slang.txt` (+ встроенный словарь как fallback). Диагностика остаётся.
Модульный `modules.lyrics_gen` **не создавать** — это была бы четвёртая точка генерации текста.

**Тест:** файл со сленгом → строки попадают в `trends`; отсутствие файла → `diagnostics`
`local_slang: FileNotFoundError`, встроенный fallback работает.

### T11 — `quality_mode` (Fast/Quality/Max) действительно влияет
**Файлы:** `app/core/recipe.py`, `app/core/stages/texture.py`,
`app/core/stages/master.py`, `modules/mastering/{stands,chain}.py`,
`modules/rvc_trainer.py`, `app/core/orchestrator.py`

Три реальные точки (только они достижимы из пайплайна):

1. **MusicGen:** `_stage_texture(..., quality_mode)` → `generate_texture(..., quality_mode=)`
   → `choose_size()` выбирает `small/medium/large`.
2. **Мастеринг:** `master_all_stands(..., iterations)` → `_master_stand_job` (кортеж +
   `iterations`, остаётся picklable) → `master_one(..., iterations=None)` →
   `_converge_loudness(search_iterations=iterations or 6)`.
   `fast→1`, `quality→3`, `max→5`.
3. **RVC-эпохи:** `retrain_incremental(..., epochs=None)`; вызывается только вручную
   (`voice_vault.maybe_trigger_retrain`), пайплайн обучение не запускает — это
   фиксируется в докстринге и в CHANGELOG, чтобы `rvc_epochs` не выглядел магией.

После этого `quality_profile` обретает читателя → `T2` зелёный.

**Тесты:** `profile["mastering_iterations"]` доезжает до `_converge_loudness`
(argcapture); `quality_mode="fast"` → `choose_size == "medium"` на CPU;
`master_one()` без аргумента ведёт себя как раньше (6 итераций).

### T12 — `n_verses` доезжает до шаблонного fallback
**Файлы:** `app/core/stages/lyrics.py`, `tests/test_lyrics_fallback_verses.py`

- `_fallback_lyrics(theme, genre, n_verses=2)` → `verse1..verseN`
  (шаблон `verse2` циклически переиспользуется, строки не дублируются буквально);
- `_struct_to_text` рендерит произвольное число куплетов в порядке ключей;
- `_text_to_struct` по-прежнему отдаёт `verse1/verse2`, но добавляет `verses` (список)
  для совместимости с новым рендером.

**Тесты:** `n_verses=1` → нет `[verse 2]`; `n_verses=4` → 4 блока; значения вне 1..4
клампятся; `theme` по-прежнему подмешивается в первую строку.

### T13 — «Три варианта» = три аранжировки, а не три громкости
**Файлы:** `app/gui/wizard/steps_run.py`, `app/core/recipe.py`,
`app/core/stages/prep.py`

`variant` уже принимает `build_arrangement`; после T5 он доезжает до плана
(`_variant_energy` меняет энергию секций). В `three_variants()` убрать подмену
`aggression` (она не должна маскировать отсутствие вариантов), оставить
`variant = 1..3` и в отчёте показывать `plan.variant`.

**Тесты:** три рецепта с `variant=1/2/3` и одинаковым seed → планы различаются
(энергия хотя бы одной секции), `beat.wav` различается по SHA-256.

---

## Ф3. P2 — тихая деградация, безопасность, метрики

### T14 — Апдейтер: безопасная распаковка (zip-slip) и сохранность данных
**Файлы:** `updater/install.py`, `updater/userdata.py`,
`tests/test_updater_safety.py`

- `_safe_extract(zip, target)`: отклоняет записи с абсолютным путём, `..`,
  симлинками; распаковывает вручную (`z.open` + `shutil.copyfileobj`);
- `USER_PRESERVED`: `"secrets.enc"` → `"data/secrets.enc"`,
  `"settings.json"` → `"data/settings.json"` (плюс сохранить старые имена для миграции);
- `verify_zip` дополнительно проверяет, что все имена путей относительны.

**Тесты:** zip с `../evil.txt` и `/abs/x` → `ok: False`, файлы вне цели не созданы;
установка на «песочный» `ZSMM_PROGRAM_DIR` с `data/secrets.enc` → файл на месте после
`install_from_zip` (с подменённым `--smoke`).

### T15 — Единая политика сети
**Файлы:** `app/core/net_policy.py` (новый), `agents/sample_hunter/hunter.py`,
`app/gui/wizard/steps_tuning.py`, `modules/freesound_client.py`, `updater/checks.py`,
`tests/test_offline_network_policy.py` (расширение)

- один хелпер `network_allowed(allow_online=False, settings_path=...)` — строгий `is True`;
  `freesound_client.online_enabled` делегирует в него;
- `hunt(allow_online: bool = False)`; чекбокс в GUI по умолчанию **выключен**,
  с подписью «разрешить сетевой поиск»;
- при попытке онлайн-поиска без разрешения — `offline: True` в результате (как у Freesound).

**Тесты:** `hunt()` без флага не обращается к сети (мок `requests.get` не вызван);
`allow_online=True` → вызван; `{"network": {"online": "true"}}` (строка) → **не** разрешает.

### T16 — Веса моделей не скачиваются неявно
**Файлы:** `app/ai/registry.py`, `app/core/musicgen_texture.py`,
`tests/test_model_loading_offline.py`

Для `MusicGen.get_pretrained`, `get_model("htdemucs")`, `ClapModel/ClapProcessor.from_pretrained`,
`DiffusionPipeline.from_pretrained`, `TTS(model_name=...)`:
локальный preflight — если весов нет в `data/ai_models/<role>`, возвращать
`FileNotFoundError("локальные веса не найдены; см. tools/pull_ai_models.py --role …")`
**до** обращения к сети; скачивание — только при `ZSMM_ALLOW_MODEL_DOWNLOAD=1`.

**Тесты:** мок `huggingface_hub` фиксирует отсутствие вызовов; без флага — исключение с
подсказкой; с флагом — путь к загрузке.

### T17 — Индикатор готовности не считает «файл есть» связностью
**Файлы:** `tools/readiness/{inventory,probes,scoring}.py`, `docs/PROJECT_STATE`-генерация

- `production_references` не учитывает вхождения в `tools/` и в самом файле;
- добавить статус `DEPRECATED` с весом 0.25 и заполнить его списком из §5.16 отчёта;
- пересчитать caps/веса так, чтобы процент падал при недостижимом коде.

**Приёмка:** `python -m tools.readiness --json` — `PLANNED`+`DEPRECATED` ≥ 15 модулей,
процент не выше 65 (с зависимостями), состав списка совпадает с BFS из отчёта.

### T18 — ID3: реализовать теги (решение владельца — вариант A)
**Файлы:** `modules/release/export.py`, `app/ai/quality/metadata.py`,
`tests/test_release_id3.py`

- после копирования мастера в релизный каталог — `EasyID3` на **копию**
  (`release/master.wav`): `title`, `artist`, `album`, `genre`, `date`, `tracknumber`;
- **оригинал мастера в проекте не мутируется** — тест сравнивает SHA-256 оригинала до/после;
- если `mutagen` недоступен или формат не WAV/MP3 — пакет собирается без тегов,
  в `manifest.json` пишется `id3: {"ok": false, "reason": ...}` (честный отказ, не тишина);
- `modules/health.py` и i18n остаются как есть: обещание теперь соответствует коду.

**Тесты:** `export_release` → `mutagen.File(master).tags` содержит `title/artist/genre`;
SHA-256 проектного мастера не изменился; без `mutagen` (monkeypatch `HAS_MUTAGEN=False`) →
`ok: True`, `id3.ok: False` с причиной.

---

## Ф4. Документация и гигиена

### T19 — Синхронизировать `docs/ARCHITECTURE.md` и `docs/WORKFLOW.md`
5 шагов, 15 стадий, реальные цифры, `app/ai/quality/` как пакет, `config/genres_100.json`
вместо `data/genres/`, `data/genre_presets/` как единственный каталог пресетов,
ссылка на `docs/PROJECT_INVENTORY.md`. Закрывается тестом `T3`.

### T20 — Разгрузить самые длинные функции
Порядок по убыванию риска (только там, где есть тесты для прикрытия):
`orchestrator.run_full_pipeline` (315) → `_run_music_block` / `_run_vocal_block` /
`_run_finalize`; `stages/beat._synth_beat` (259) → `_drum_lane` / `_bass_lane` / `_fx_lane`;
`beat/constructor.build_track` (243) → оставить, но вынести рендер секции.
Правило ≤ 60 строк вводится как **мягкое** (тест фиксирует список исключений с
комментарием), иначе правка превращается в переписывание.

### T21 — Упаковка и зависимости
`build.yml` собирает через `packaging/zsmm.spec` (один источник правды); из
`requirements.txt` убрать 8 пакетов без импортов (`matplotlib`, `audioread`, `click`,
`omegaconf`, `plyer`, `mingus`, `tqdm`, `mutagen` — последний только если T18-вариант B);
удалить/пометить `tools/quality_gate.sh` как неактуальный (нет `mypy`/`pylint`).

### T22 — CHANGELOG и PROJECT_STATE
Запись по каждому пункту с причиной и способом проверки; PROJECT_STATE пересобрать
из `tools/readiness --json` после T17 (без ручных цифр).

---

## Ф5. Верификация

### T23 — Финальная матрица

| Гейт | Требование |
|---|---|
| `pytest tests/ -q` | ≥ 840 passed + новые тесты, 0 failed |
| покрытие | ≥ 61 %, и ≥ 60 % у `updater/` и `modules/render_queue.py` (сейчас 15 % и 0 %) |
| `compileall` | 0 ошибок |
| `ast_dead_imports`, `audit_honesty`, `fallback_audit`, `gitignore_guard` | зелёные |
| `tools/samples_audit`, `audit_data_inventory`, `genre_validator` | без изменений (32 сэмпла, 105 файлов, 50/119) |
| `tools/smoke_audio` | 6/6 PASS, LUFS/TTP в допуске |
| `tools/smoke_god` | 8/8 PASS |
| `main.py --run --seed 42` | PARTIAL ≥ 87 %, стадия arrangement непуста |
| `main.py --e2e` | PARTIAL, 8/8 мастеров, 9+ файлов релиза |
| `--readiness --json` | процент не завышен по сравнению с BFS-связностью |

Плюс ручная проверка воспроизводимости: `seed=7` дважды → идентичные `beat.wav`,
`texture_scaffold.wav`, `report.json.stages[].output.plan` (план — тоже).

---

## 2. Что в план **не** входит (и почему)

| Не делаем | Причина |
|---|---|
| Проверка GUI, микрофона, Windows 11 | Нет целевой машины и `libGL` в песочнице; остаётся в `ROADMAP.md` как задача владельца |
| Реальный inference MusicGen/XTTS/RVC/Demucs/CLAP/SDXL | Нет весов и GPU; тестируем только контракты загрузки и отказы |
| Субъективное качество музыки | Требует слепого прослушивания (`docs/BLIND_LISTENING.md`) живыми людьми |
| Подключение `expert_mode`, `kpi_monitor`, `tiktok_edit`, `video_edit` к UI | Продуктовое решение; в Ф3 они честно помечаются `DEPRECATED`, а не «включаются ради галочки» |
| Удаление legacy-модулей (`sidechain.py`, `mastering_chain.py`, `pipeline_core.py`) | Решение владельца: **пометить `DEPRECATED`**, код оставить. Удаление — отдельной итерацией после того, как пометка проживёт один релиз |

---

## 3. Риски

| Риск | Митигация |
|---|---|
| Подключение `build_arrangement` меняет звук существующих прогонов | T6 фиксирует контрольные SHA-256 до правки; при расхождении на дефолтах — план передаётся только как метаданные, влияние на бит отключается флагом `ZSMM_ARRANGEMENT_DRIVES_BEAT` |
| `master_one(..., iterations=)` усложняет pickling стендов | Аргументы остаются кортежем примитивов; тест `test_mastering_capability_isolation.py` и `test_mastering_gates.py` — регрессия |
| Ужесточение `T1`/`T2` валит существующие тесты | Сначала включить гейты с `xfail`-маркером на известные нарушения, снять маркер по мере T5/T11 |
| Правка `USER_PRESERVED` ломает обновление со старых версий | Старые имена остаются в списке, добавляются новые пути |

---

## 4. Порядок коммитов

```
test(guards): T1-T3 контракты стадий, рецепта и документации
fix(sample_hunter): T4 восстановлены импорты и диагностика
feat(arrangement): T5-T6 планировщик подключён к пайплайну и биту
fix(runtime): T7 render_queue и ночное обучение
fix(video_edit): T8 fallback WAV и импорты
fix(voice): T9 мёртвый флаг HAS_LIBROSA
fix(trends): T10 источник локального сленга
feat(quality): T11 quality_mode влияет на генерацию
fix(lyrics): T12 n_verses в шаблонном fallback
feat(variants): T13 варианты = разные аранжировки
fix(updater): T14 zip-slip и сохранность данных
refactor(net): T15 единая политика сети
fix(ai): T16 явный отказ без локальных весов
fix(readiness): T17 связность вместо «файл есть»
feat(release): T18 ID3 по решению владельца
docs: T19-T22 синхронизация и гигиена
chore(release): T23 верификация и CHANGELOG
```

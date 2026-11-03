# CHANGELOG

> Актуальная версия: **41.0.0-alpha.15** (2026-11-03). План рефакторинга —
> `docs/PLAN_v41_MASTER.md`, состояние — `PROJECT_STATE.md`.
> История до v40 сохранена ниже как архив: удалённый `SESSION_LOG.md` больше не поддерживается.

## 41.0.0-alpha.15 — визард 5 шагов, единый журнал, упаковка (2026-11-03)

- **Визард сведён к пяти шагам** (`app/gui/wizard/`): жанр и тема → материал →
  голос → тонкая настройка → запуск, плюс экран результата со «пересобрать»,
  «три варианта», «ещё» и папкой релиза. Удалены `steps_intro.py` и
  `steps_creative.py` (дублировали друг друга), вместо них — `steps_brief.py`,
  `steps_material.py`, `steps_voice.py`, `steps_tuning.py`, `steps_run.py`,
  `record_dialog.py`, `dialogs.py` (`AIStatusDialog`).
- **i18n без «строк мимо словаря»**: тексты вынесены в `app/core/i18n_data.py`
  (`TRANSLATIONS` ru/en, ключи `menu.*`, `nav.*`, `pipeline.*`, `status.*`,
  `wizard.*`, `dialog.*`), тест проверяет одинаковый набор ключей у обоих языков
  и что в UI не осталось литеральных подписей.
- **Логирование: одна реализация вместо двух.** `app/logger.py` удалён,
  всё в `app/core/logger.py`: каталог `ZSMM_LOG_DIR` → `%LOCALAPPDATA%\ZS Music
  Maker\logs` → `~/.local/share/zs-music-maker/logs` → `output/logs`, ротация
  10 МБ × 5, редакция секретов, `SafeStream` для cp866-консолей, идемпотентный
  `setup_logger`, `write_crash_report` + `install_excepthook` (`crash_*.txt`
  с трейсбеком, прежний hook сохраняется), `TerminalStageProgress`. Причина:
  старая копия писала в `logs/` относительно текущего каталога и при запуске
  с ярлыка журналы просто терялись.
- **Упаковка под Windows 11**: `packaging/zsmm.spec` (PyInstaller onedir,
  `console=False`, в бандле `data/`, `docs/`, `scripts/`, `version.json`,
  `VERSION`, `INSTALL.md`, `LICENSE`, тяжёлые AI-пакеты исключены; onefile
  только через `ZSMM_ONEFILE=1` — он распаковывается при каждом старте и
  противоречит цели «старт < 5 с»). Скрипты: `setup.cmd` (проверка Python ≥ 3.11,
  venv, зависимости, `--health`), `run_silent.cmd` (pythonw, без окна консоли),
  `run.cmd`, `build_exe.cmd` (+ smoke `--version` собранного exe),
  `verify.cmd` (compileall → pytest → смоуки → аудиты → `--readiness`),
  `make_shortcut.ps1`.
- **Честный прогресс и частичная пересборка.** `run_full_pipeline(...,
  on_stage=...)` вызывает колбэк после каждой стадии; `runtime_orchestrator`
  переводит его в `job.progress` (5 % на старте, 95 % в конце), так что полоска
  в визарде больше не «прыгает» с 0.1 на 0.92. `total` берётся из
  `STAGE_RECORDS` — пропущенные стадии тоже попадают в отчёт как `BLOCKED`,
  поэтому счётчик всегда сходится с отчётом. Мёртвый флаг рецепта
  `rebuild_only` (писался и никогда не читался) заменён рабочим `only`;
  «пересобрать только вокал/мастер» действительно пропускает остальные стадии.
- **Инвентарь готовности устойчив к грязному индексу**: `tracked_python_modules`
  фильтрует файлы по наличию на диске, иначе удалённый, но ещё не
  закоммиченный модуль ронял `tools/readiness` и три теста.
- **Один конвейер вместо трёх.** `--god` и `--async` больше не собирают свою
  музыку: `orchestrator_god.py` (243 → ~100 строк) стал адаптером над
  `run_full_pipeline` (длина 120 с + отчёт в прежней форме), `orchestrator_async.py`
  (118 → ~120) исполняет тот же прогон в рабочем потоке и отдаёт стадии списком
  `AsyncStage`. Ушли `beat_constructor`+`phonk_engine`-«колокольчики» и
  мастеринг в −12 LUFS, из-за которых `--god` звучал иначе, чем обычный прогон
  и не получал гейтов качества.
- **Мастеринг восьми стендов считается параллельно**: `ProcessPoolExecutor`
  (до `min(cpu, 4)` воркеров, `ZSMM_MASTER_WORKERS=1` — последовательно,
  фолбэк при недоступности пула). На 120-секундном треке измерено
  349.5 с → 180.9 с на двух ядрах; звук **побитово тот же** (max |diff| = 0.0,
  те же LUFS/TP/гейты, `tests/test_mastering_parallel.py`). `main.py` вызывает
  `multiprocessing.freeze_support()` — без него собранный exe при порождении
  процессов перезапускал бы сам себя.
- Новые тесты: `tests/test_logger_and_crash.py` (10), `tests/test_wizard_structure.py`
  (10), `tests/test_windows_entrypoints.py` (17), `tests/test_pipeline_progress_contract.py`
  (4), `tests/test_orchestrator_adapters.py` (8), `tests/test_mastering_parallel.py` (3). Полный набор: **523 passed, 1 skipped**; `smoke_audio` 6/6, `smoke_god` 8/8,
  аудит честности CLEAN, AST CLEAN, gitignore CLEAN.

## 41.0.0-alpha.14 — точный true-peak, демо-прогон, property-тесты (2026-11-03)

- **Главный баг мастеринга найден и устранён: true-peak мерился неверно.**
  `metrics.true_peak_dbtp` передискретизировал только 48 самых громких участков
  по сэмпловому пику. На клиппированном материале все пики равны по амплитуде, а
  межсэмпловый перегруз гуляет от участка к участку: там, где честное 4× давало
  **+0.37 dBTP**, старый метод показывал **−1.00 dBTP**. Лимитер «прятался» на
  3–4 дБ ниже потолка, громкость потом добивалась клиппингом (16 % сэмплов), а
  файл всё равно выходил за потолок. Теперь буфер режется на окна по 10 с с
  запасом 256 сэмплов — результат совпадает с полным 4× до 0.01 дБ, память в
  мегабайтах, 75-секундный стереофайл считается за 0.6 с.
- **Лимитер строит усиление по 4×-огибающей** (`_oversampled_envelope`), а не по
  сэмпловому пику с «подтягиванием» всего буфера вниз. Итог на том же миксе
  (клубный стенд): было −9.16 LUFS при 16 % клиппинга, стало **−8.70 LUFS при
  4.3 %** и TP ровно −1.00 dBTP; время мастеринга одного стенда упало со 131 с
  до 20 с.
- **Де-нойз вокала — своя реализация вместо `noisereduce`.** Спектральные
  воротца на numpy: профиль шума = средняя мощность самых тихих 20 % кадров,
  маска сглажена по времени и частоте, подавление ограничено −12 дБ (это не
  гейт). Измерено на синтетическом вокале: сибилянты −3.06 дБ (их снимает
  де-эссер), воздух 11–13 кГц **−0.11 дБ** (не глушится), пауза −81.8 dBFS,
  4-минутный файл обрабатывается за 6.9 с. `noisereduce` убран из
  `requirements.txt` и `pyproject.toml` — импортов больше нет.
- **Вокал пишется в 32-bit float.** `_write` вокальной цепочки и
  `voice_cleaner` писали промежуточные стадии в PCM_16: пять последовательных
  записей накапливали шум квантования. Теперь `FLOAT`, тест это фиксирует.
- **Пять демо в пяти жанрах — все гейты зелёные** (`tools/generate_demos.py`,
  `output/demos_run/demos/demos_report.json`): drift_phonk, trap, house,
  hard_rock, dark_ambient. Микс §7.2 — 5/5 у всех; мастеринг — 8/8 стендов у
  всех; стриминговые мастера ровно **−14.0 LUFS** при TP −1.0…−1.05 dBTP; клуб
  −8.63…−8.74 LUFS; bluetooth −14.5…−14.74 LUFS; hit-score **74.3…78.6**
  (verdict `solid` при пороге 70). `BLOCKED` — только отсутствующие тяжёлые
  зависимости (torch/audiocraft/stems), ни одного `FAILED`.
- **Property-тесты DSP (п. 6.3).** `tests/test_dsp_properties.py`: 13 тестов на
  hypothesis — фильтры/полки, лимитер (потолок и длина), soft-clip (identity
  ниже колена), компрессор, ширина, тюн, де-эссер, метрики на тишине и одном
  сэмпле. Тесты сразу нашли два реальных бага: падение `mid_side` на моно-входе
  формы `(N, 1)` и «раздувание» gain-огибающей де-эссера на буферах короче ядра
  сглаживания (`np.convolve("same")` возвращал длину ядра).
- **Двойное покрытие тестами вокальных эффектов.** `tests/test_vocal_fx_double_throw.py`:
  double-tracking и delay throw проверяются на реальных WAV — длина, потолок,
  рост энергии, «не копия», моно-вход, отсутствие файла, бросок только в паузу.
  Покрытие `modules/vocal_fx/double.py` 41 % → 100 %, `throw.py` 9 % → 100 %.
- **Зависимости разработки вынесены.** `requirements_dev.txt` (pytest,
  hypothesis, pytest-cov) + установка в CI и в `INSTALL.md` §4. Владельцу на
  Windows для работы программы это не нужно.

## 41.0.0-alpha.13 — anti-neuro вокал без pydub (2026-11-02)

- **Одна реализация вместо двух.** `modules/anti_neuro.py` (397 строк с pydub,
  ffmpeg-зависимость и молчаливый уход в fallback) переписан на numpy +
  soundfile: 380 строк чистого DSP, зависимостей от ffmpeg нет вовсе. На чистой
  Windows-машине без ffmpeg раньше весь этот этап фактически не работал.
- **Длина вокала сохраняется всегда.** Старый путь клеил 180 мс шума в начало
  файла — вокал съезжал относительно сетки микса. Теперь вдохи добавляются
  аддитивно **в существующие паузы** между фразами (`breaths_in_pauses`,
  измерено: 2 вдоха в двух паузах, таймлайн не меняется).
- **Стадии и их смысл:** `consonant_boost` (+3 дБ к 3–10 кГц только в моменты
  атак — согласные читаются, «стеклянный» верх не поднимается),
  `de_plastic` (срез ультразвука нейросети выше 15.5 кГц),
  `human_error` (микропровалы −6…−10 дБ и микро-детюн ±4 цента),
  `entropy_boost` (у второй половины подрезан низ — «второй куплет» не копия).
- **Честные отчёты:** каждая стадия попадает либо в `stages_applied`, либо в
  `skipped` с причиной; `length_preserved` проверяется по числу сэмплов.
- **Тесты:** `tests/test_anti_neuro_vocal.py` (6) — детерминизм по seed,
  сохранение длины, вдохи только в паузах, отказ на битом входе, отсутствие
  импорта pydub (AST-проверка). Итого **433 passed**.

## 41.0.0-alpha.12 — вокальная цепочка, мастеринг без «качелей» (2026-11-02)

- **Тюн вокала (4.4.1).** `modules/vocal_fx/pitch.py`: детекция F0 по
  нормированной автокорреляции (кадр 40 мс, шаг 10 мс, 70–1000 Гц,
  параболическая интерполяция), квантизация к тонике и ладу (major, minor,
  harmonic minor, phrygian, dorian, pentatonic) с адаптивной силой: вибрато
  правится мягко, грубая фальшь — почти полностью, сдвиг ограничен 100 центами.
  Ресинтез фазовым вокодером с identity phase-locking и обратным
  пересэмплированием по монотонной карте. Замер на синтетике: 0 % → 99.7 %
  кадров в тоне, отклонение 65 → 0.8 цента, RMS и пик сохраняются, длина
  совпадает до семпла.
- **Де-эссер (4.4.2).** `modules/vocal_fx/desser.py` реагирует на **долю**
  полосы 4.5–9.5 кГц в общем сигнале, а не на абсолютный уровень: шипящие
  снимаются на 5.4 дБ, гласные участки не меняются вовсе (разница −240 дБ).
  Полоса выделяется по FFT (нулевая фаза) — иначе вычитание полосы возвращало
  фазоискажённую копию и де-эссер был не слышен.
- **Просодия (4.4.3).** `modules/vocal_fx/prosody.py`: детекция фраз по
  огибающей, выравнивание уровня фраз в пределах ±6 дБ, приглушение дыхания в
  паузах до −24 дБ с 30 мс рампами, притяжка атак к сетке 1/16 не дальше
  30 мс. В синтетическом тесте: 3 фразы, 2 паузы, сдвиг 13.3 мс.
- **Цепочка целиком.** Порядок `clean → tune → deess → prosody → double →
  throw`; каждый шаг честно попадает в `stages` или в `skipped` с причиной.
  Вокальная ветка получает BPM и тональность из бита: тюн настраивается на ту
  же гамму, в которой сыгран инструментал.
- **Мастеринг: громкость и плотность без конфликта (4.6).** Сведение громкости
  теперь отбрасывает кандидатов, у которых crest выходит из коридора стенда;
  «стать тише» делается линейным тримом (crest не меняется), «стать громче» —
  новым рендером. Если crest выше нормы — мягкий клиппер, затем компрессия
  тела. Коридор корреляции задан по стендам: на плотных (клуб, тачка, TikTok,
  Bluetooth) лимитер поднимает корреляцию закономерно, картинку задаёт микс.
  Итог на реальном прогоне: **8/8 стендов зелёные** (streaming −14.0 / TP −1.0,
  club −8.5 / crest 6.6, car −10.0, bluetooth −14.5 / crest 13.7).
- **Микс.** Ширина микса теперь целится в корреляцию 0.72, а не в границу 0.8:
  мастер с 0.79 после лимитера вылетал за коридор.
- **Тесты.** +13 к вокальной цепочке, обновлены тесты мастеринга. Итого
  **427 passed**.

## 41.0.0-alpha.11 — anti-neuro, референс-матчинг, аудит честности (2026-11-02)

- **Микро-вариативность повторов (план 4.7.1).** `modules/beat/variation.py`:
  `bar_variant()` детерминированно (RNG конструктора) выбирает изменения
  рисунка для каждого такта — пропуск хэта, добавочный офф-бит хэт, ghost-нота
  малого, дыхание уровня ±0.3 дБ. Сильные доли (0/4/8/12) неприкосновенны,
  поэтому грув остаётся узнаваемым.
- **Тест «формульности» (4.7.3).** `repetition_report()` считает энтропию типов
  тактов по четырём признакам (RMS, спектральный центроид, баланс низ/верх,
  плотность атак) и среднее сходство соседних тактов. Измерено на реальном
  бите (40 с, seed 5): энтропия 0.65 нормированной, 8 типов тактов,
  сходство соседей 0.30, `formulaic=False`.
- **Дрейф темпа ±0.2 % и шум комнаты (4.7.2).** `modules/beat/microtime.py`:
  плавный дрейф читается интерполяцией с сохранением длины (пиковое отклонение
  26.8 мс на 40 с) плюс шумовой пол −62 dBFS с ограничением полосы.
  `build_track` возвращает `humanity` и `repetition` в отчёте.
- **Референс-матчинг микса (4.5.4).** `modules/mix/reference.py`: профиль по
  9 октавным полосам, коррекция ±9 дБ с точной реконструкцией полос
  (`apply_band_gains`), либо matchering, если он установлен; отчёт
  `reference_match_report.json` с отклонениями до/после по каждой полосе,
  LUFS и crest. Гейт: отклонение профиля после матчинга ≤ 2.5 дБ. Стадия микса
  берёт первый референс из рецепта автоматически.
- **Защита такта вместо деления на пик.** Перегруз такта теперь ограничивается
  мягким клиппером на −3 dBFS: ниже колена сигнал идентичен, «качки» уровня
  от такта к такту нет.
- **Аудит честности (план 6.6).** `tools/audit_honesty.py` — AST-проверка
  немых `except: pass`, `except: ...`, `return` без лога и маркеров подделки
  (`fake`/`simulate`/`stub`/`dummy`) в проде. Все **54** найденных немых
  обработчика заменены на логированные: отчёт CLEAN, гейт в
  `tests/test_honesty_audit.py`, инструмент добавлен в `test_tools_cli.py`.
- **Эталоны пересчитаны** под новый характер бита: golden-beat RMS 0.160,
  centroid 5.2 кГц, корреляция 0.868.
- **+18 тестов:** `test_beat_variation.py` (8), `test_mix_reference.py` (6),
  `test_honesty_audit.py` (3), обновлённые аудио-гейты. Итого 405 passed.

## 41.0.0-alpha.10 — микс и мастеринг по-настоящему (2026-11-02)

- **Единый измерительный слой `modules/dsp`.** `metrics` (RMS, peak, true-peak
  4× по окрестностям пиков, LUFS по BS.1770, crest, корреляция, потеря в моно),
  `filters` (хайпасс/полка/точное деление полос), `dynamics` (канальный и
  двухполосный компрессор на контрольной частоте), `limiter` (look-ahead
  лимитер с гарантией −1 dBTP + мягкий клиппер). Раньше каждый файл считал
  эти метрики по-своему — теперь одна ответственность = один модуль.
- **Пакет `modules/mix` (план 4.5).** `staging` — gain staging шины к −18 dBFS
  по опорному (самому громкому 10-секундному) участку с потолком −3 dBFS;
  `ducking` — сайдчейн kick → низ шины только ниже 120 Гц (верх не трогается);
  `width` — mid/side ширина с приведением корреляции в коридор 0.2…0.8
  (и честный отказ от «изобретения» стерео из моно); `bus` — сборка шины,
  контроль крest-фактора лимитером и `mix_report.json` с гейтами §7.2.
  Стадия `_stage_mix_and_sidechain` стала адаптером над этим пакетом.
- **Мастеринг сведён к одному движку `modules/mastering` (план 4.6).**
  Тон стенда → двухполосная компрессия → мягкий клиппер → look-ahead лимитер
  −1 dBTP → сходимость по LUFS (калибровка на громком фрагменте + доводка).
  Цели: streaming −14 ± 0.5, клуб −8.5, тачка −10, TikTok −11.5; на каждом
  стенде пишутся true-peak, crest, корреляция, потеря в моно, клиппинг и флаг
  `gates_passed`. `mastering_chain` превращён в тонкий legacy-адаптер.
- **Замерено на реальном прогоне** (`main.py --run --seed 11`, 90 с трек):
  микс — все 5 гейтов зелёные (опорный RMS −18.0 dBFS, crest 12.1 дБ,
  корреляция 0.66, true peak −4.88 dBTP, 0 клиппов); мастеринг — **8/8 стендов
  зелёные** (streaming −14.04 LUFS, club −8.50 LUFS при crest 4.45, tiktok
  −11.27, car −10.29, остальные −14.1…−14.7, true peak ≤ −1.0 dBTP).
- **Починена anti-neuro полировка.** `_micro_timing_jitter` и соседние эффекты
  проверяли `np is None`, хотя numpy импортирован как `_np` → стадия всегда
  падала в FALLBACK с NameError; lofi-фильтр падал на sr < 32 кГц
  (срез 16 кГц выше Найквиста). Теперь полировка реально работает,
  детерминирована по seed и возвращает мастер к −14 LUFS.
- **`pyproject.toml`: секция `[tool.pytest.ini_options]`** — `testpaths`,
  `--strict-markers`, маркеры `audio/slow/gui/e2e` (план 0.4).
- **+25 тестов:** `test_dsp_metrics.py` (true-peak сверен с полной
  передискретизацией), `test_mix_bus.py` (гейты микса, сайдчейн, ширина,
  отчёт), `test_mastering_gates.py` (LUFS/пик/отчёт по стендам),
  `test_anti_neuro_track.py` (регресс на NameError). Итого 394 passed.

## 41.0.0-alpha.9 — контраст дропа по низу (2026-11-01)

- **Измеренный контраст низа ≥6 дБ.** В куплете низ «суше» (сплит бара на
  <120 Гц и трим `LOW_TRIM` 0.55), в дропе трим 1.0 плюс саб-хвост под каждый
  кик (41 Гц) и отдельный саб-слой на октаву ниже баса. Замерено на трёх
  жанрах: 6.7–7.6 дБ (было 4.2 дБ).
- `bass_gain` в отчёте секций, `dramaturgy` показывает трим по низу.
- Гейты: `tests/test_beat_drop_contrast.py` — контраст ≥6 дБ в phonk/trap/
  tech-house, слышимый провал перед первым хуком, порядок тримов.

## 41.0.0-alpha.8 — драматургия трека (2026-11-01)

- **`modules/beat/dramaturgy.py`** — структура вместо жёстких 8/4/8 тактов:
  `plan_sections()` раскладывает 2:30–3:30 на intro → куплет/предприпев/припев
  (×N) → бридж → припевы → аутро; короткий заказ укорачивает структуру, а не
  растягивает трек.
- **Энергия и гейн секций:** `SectionPlan.gain_db` (−12 … 0 дБ) вместо списка
  констант в аранжировке. Разница припев/куплет ≥4 дБ гарантирована тестом.
- **Правило TikTok-входа:** мотив хука играет в интро (слой `hook_lead`),
  поэтому хук слышен с 0-й секунды, а не с 46-й.
- **Потолок плотности:** `layers_for_section()` — 3 слоя в интро, 5 в куплете,
  7 в припеве; в куплете хук-лид молчит (анти-«каша»).
- `dramaturgy` в результате сборки бита: структура, энергия, начало хука,
  контраст дропа, максимум слоёв.
- Гейты: `tests/test_beat_dramaturgy.py` — 6 проверок (длина, структура,
  хук ≤15 с, контраст ≥0.3 и ≥4 дБ, потолок слоёв, отчёт в результате).

## 41.0.0-alpha.7 — грув из референса (2026-11-01)

- **`modules/groove_extractor.py`: измеренные смещения ударов.** Новый
  `_attack_envelope` (RMS первой разности, шаг 1 мс) и `_kick_attack_offsets_ms`:
  для каждой шестнадцатой ищется атака в окне ±35 % шага, по тактам берётся
  медиана. Низкочастотная огибающая для микротайминга не годилась — у 49-герцового
  кика RMS набирается 10–20 мс и смещение уезжало вместе с ней.
- `groove_template` теперь содержит `timing_offsets_ms` (16 значений) и
  `timing_confidence`; хвосты предыдущих ударов и «плоские» окна отбрасываются.
- **Конструктор бита применяет рисунок референса:** `groove["timing_offsets_ms"]`
  главнее стандартного «человеческого» джиттера (ограничение ±20 мс), иначе
  остаётся обычный живой тайминг ±9 мс.
- Гейты: `tests/test_groove_reference_timing.py` — синтетический референс с
  бочкой на 8 мс позже сетки восстанавливается с точностью ±4 мс и переносится
  в бит.

## 41.0.0-alpha.6 — ритмические семейства вместо трёх пресетов (2026-11-01)

- **`modules/beat/patterns.py` переписан:** 15 ритмических семейств (phonk,
  drift, trap, drill, boom-bap, house, tech-house, dnb, jersey, reggaeton,
  afrobeat, amapiano, lofi, hyperpop, hardstyle) вместо трёх захардкоженных
  пресетов. Каталог из 50 жанровых пресетов проецируется на семейства по
  ключевым словам — новый жанр сразу получает осмысленный грув.
- **Velocity-карты:** профиль акцентов на семейство (сильная/слабая доля, «и»,
  три уровня хэта) плюс ручные карты для phonk/trap/house/drill/reggaeton.
  Громкость удара = акцент семейства × человеческий джиттер.
- Бас больше не дублирует бочку ни в одном семействе (в house — оффбит, в
  trap — с задержкой на «и», в hardstyle — рваный).
- `groove_family` в результате сборки бита, `family_summary()` для отчётов.
- Гейты: `tests/test_beat_pattern_families.py` — все жанры каталога получают
  семейство, семейства не дублируют друг друга, velocity-карты не вырождаются
  в константу, override грува по-прежнему главнее пресета.

## 41.0.0-alpha.5 — сэмпловый банк и релизный пакет (2026-11-01)

### Added — Этап 4.1: сэмпловый банк
- **`app/audio/samples.py`** — фундамент «живого» звука: манифест
  `data/samples/manifest.json` (схема `zsmm.sample-bank.v1`), velocity-слои,
  round-robin, ресемплинг, питч-шифт под тонику и гранулярный тайм-стретч.
  Только CC0/CC-BY/public-domain проходят в бит; всё остальное помечается
  `REJECTED` и не звучит. Пустой банк — честный `FALLBACK`.
- **`tools/samples_audit.py`** — аудит лицензий, SHA-256, покрытия, ≥3 слоёв и
  ≥2 вариантов на инструмент; отчёт `output/samples_audit.json` и генерация
  `licenses.txt` для релиза.
- `data/samples/README.md` — как добавить чистый банк (поля license/source/sha256).
- Бит берёт сэмплы из банка первыми: `drum_engine.status` становится
  `REAL_PASS`, когда покрыто ≥4 из 6 барабанных инструментов.

### Added / Fixed — релизный пакет
- **`modules/release/`** восстановлен: экспорт с манифестом SHA-256 и ZIP,
  полный пакет (мастер-стенды, стемы, lrc/srt, отчёт хита), пакеты площадок
  Spotify / Яндекс-VK / TikTok / YouTube / Shazam, честный статус ISRC.
- **`.gitignore` починен:** правило `release/` (без якоря) молча игнорировало
  пакет `modules/release/`, и модуль выпал из репозитория. Теперь `/release/`.
- **`tools/gitignore_guard.py`** + тест: если любой каталог с кодом снова
  спрятан правилом игнора, гейт падает.
- `health`, `self_diag`, KPI-дашборд больше не ищут удалённые `*_v9/v12`-модули.

**Гейты:** 350 тестов зелёные, `smoke_audio` 6/6, `smoke_god` 8/8,
`ast_dead_imports` CLEAN, readiness 65 % (потолки: нет записи с микрофона и
тяжёлых движков).

## 41.0.0-alpha.4 — барабаны и человеческий грув (2026-10-31)

Первый шаг Этапа 4: бит перестаёт звучать как синтезатор из синусов.

- **`modules/beat/drums.py` — FALLBACK-синтез one-shot'ов.** Кик с питч-конвертом
  (165→49 Гц), кликом битера и сатурированным телом; снейр из двух мод корпуса
  (185/330 Гц) плюс шум 1.4–11 кГц; клэп из четырёх хлопков с разлётом 0–22 мс и
  «хвостом» зала; 808-хэт из шести негармонических прямоугольников (ФВЧ 6.8 кГц,
  закрытый и открытый); 808-бас с глиссандо и мягкой сатурацией; импакт дропа.
  `CAPABILITIES` честно помечает движок как `FALLBACK`, пока банк сэмплов пуст.
- **`modules/beat/humanize.py` — «человечность».** Микротайминг по инструментам
  (кик ±1.4 мс, снейр +2…7 мс, хэты −3…+2.4 мс), свинг на нечётных шестнадцатых,
  velocity ±12 % с акцентами на сильных долях, ghost-ноты, round-robin вариантов,
  сбивки в конце фразы. Удар больше не прибит к сетке гвоздями.
- **Баланс микса** (`INSTRUMENT_GAIN`), новые слоты `clap` и `open_hat` в банке
  сэмплов, `drum_engine` в результате сборки бита.
- **Гейты:** `tests/test_beat_humanize_and_drums.py` — спектр кика (≥48 % энергии
  ниже 120 Гц), яркость хэта (центроид ≥6 кГц), смещение ударов от сетки
  0.3–9.5 мс, крест 6–22 дБ, отсутствие клиппинга; `tests/test_beat_harmony.py` —
  диатоника аккордов, плавность голосоведения (≤5 полутонов), середина в пэде.
- **Измерено** на рендере 90 с: бит crest 17.3 дБ, мастер peak −2.85 dBFS,
  RMS −13.1 dBFS, crest 10.3 дБ, корреляция 0.79.
- **`modules/beat/harmony.py` — гармонический слой.** Диатонические трезвучия и
  септаккорды от тоники, прогрессии по жанрам (i–VI–III–VII, i–iv–VI–v, i–VII–VI–VII),
  голосоведение с минимальным движением голосов (без скачков на октаву, ниже 60 Гц
  не заходит — там живёт 808), аддитивный пэд с детюном/вибрато и FM-стабы на
  офф-битах. Доля середины в миксе выросла 17.7 → 20.2 %, крест 13.4 дБ.
- **Дроп стал дропом:** вместо линейного 200-мс спада — 300-мс провал по кривой
  четвёртой степени (гейт `smoke_audio` видит 15 хопов тишины вместо 7).
- **Убрана «pump»-качка:** такт больше не делится на пик при `peak > 1.0`;
  аварийный гейн включается только при реальном перегрузе (> 1.25).
- `tests/fixtures/audio/golden_beat_15s.wav` перегенерирован под новый движок,
  пороги подписи обновлены (rms 0.140–0.170, центроид 5.8–7.2 кГц, peak ≤ 0.97).
- `tools/readiness.py` → пакет `tools/readiness/` (`paths/inventory/probes/scoring/cli`),
  запуск — `python -m tools.readiness`.

## 41.0.0-alpha.3 — единый пайплайн и контракт стадий (2026-10-31)

Второй шаг Этапа 2: «один пайплайн, один формат результата стадии».

- **Контракт стадий:** новый пакет `app/pipeline/` — `StageStatus`
  (`OK / FALLBACK / BLOCKED / FAILED`), `StageResult`, `classify()` и
  `summarize()`. Вердикт и процент считаются **только** там; второй экземпляр
  модели стадии в `app/core/pipeline_core.py` удалён, `AIStage`-отчёты
  (`app/ai/sequential_runner.py`) теперь тоже несут честный `status`.
- **Оркестратор разобран:** `app/core/orchestrator.py` 2132 → 387 строк.
  Реализации стадий — `app/core/stages/{prep,beat,texture,lyrics,vocal,mix,master,release}.py`
  (каждый ≤ 320 строк), рецепт — `app/core/recipe.py`, склейка осталась в
  оркестраторе.
- **AI-пайплайн разобран:** `app/core/orchestrator_ai.py` 668 → 129 строк
  (только проводка), стадии — `app/core/ai/stages_{meta,music,vocal,final}.py`,
  рендер — `app/core/ai/render.py`, состояние — `AIContext`.
- **Свой микрофон — основной вокальный путь:** `_run_vocal_chain` берёт
  `own_vocal_wav` пользователя первой веткой, синтез идёт только при его
  отсутствии, синтетический скаффолд без RVC в мастер по-прежнему не попадает.
- **Найденные и исправленные дефекты** (были скрыты монолитными файлами):
  `_stage_analyze`/`_stage_groove` всегда падали с `TypeError` (лишний
  `q_params`); god-режим возвращал `None` вместо честного BLOCKED и ронял
  пайплайн на вокале; релиз-пакет молча уходил в минимальный фоллбек из-за
  `NameError: HAS_PYDUB`; `render_xtts_vocal`/`render_rvc_vocal` теряли импорты
  валидаторов.
- **Тесты:** добавлен `tests/test_pipeline_stage_contract.py` (16 кейсов на
  статусы, вердикты и рецепт) — всего 301 тест; smoke_audio 6/6, smoke_god 8/8.

## 41.0.0-alpha.2 — семантическое слияние дублей (2026-10-31)

Этап 2 плана: «одна ответственность — один модуль». Удалены все оставшиеся
дубли, каждая цепочка существует ровно в одном месте.

- **Тексты:** `lyrics_gen_v8` и `lyrics_gen_ai` влиты в `modules/lyrics_gen.py`
  (604 строки) — три входа (`generate_lyrics`, `generate_lyrics_ai`,
  `generate_lyrics_v8`) с общим контрактом и обязательным сохранением строк
  пользователя.
- **Мастеринг (было 6 реализаций):**
  `mastering.py` — мастеринг под 8 стендов (numpy-DSP, честные LUFS-метрики);
  `mastering_chain.py` — pedalboard-чейн трека, ceiling −1 dBTP, RMS-фоллбек;
  `mastering_reference.py` — единственный адаптер Matchering (+`master_ai`).
  Удалены `mastering_pro`, `mastering_ai`, `matchering_master`.
- **Вокал / трек:** `anti_ai_polish` влит в `anti_neuro`; затем модуль разделён
  по ответственности — вокальная цепочка (`anti_neuro.py`) и «оживление»
  микса (`anti_neuro_track.py`). `_stage_polish` пробует трековую цепочку,
  затем вокальную, и лишь потом честно копирует мастер (`fallback_used`).
- **Релиз:** `release_pack_full` + `release_export` + `distribution` → пакет
  `modules/release/` (`assets`, `text`, `pack`, `export`, `channels`, `models`)
  с ленивым публичным API. Мёртвая ветка `release_pack_v13` и её тест убраны:
  стадия релиза = один движок + честный минимальный пакет.
- **Микс:** удалён `modules/mixdown.py` (дубль канонической стадии микса
  в оркестраторе).
- **Имена:** тесты и фикстуры без версионных суффиксов
  (`test_lyrics_gen_orchestration`, `test_health_collection`,
  `test_theme_apply_observability`, `data/sample_manifests/*_test_samples.json`).
- **Гейты:** 285 тестов, `smoke_audio` 6/6, `smoke_god` 8/8, AST dead imports
  0, `compileall` 0 ошибок; устаревшие имена модулей вычищены из
  `health`, `kpi_dashboard`, `readiness`.

## 41.0.0-alpha.1 — расчистка и дедупликация репозитория (2026-10-31)

- **Репозиторий:** 1657 → 320 файлов; `docs/` 52 МБ → 3 документа + план.
  Удалены сгенерированные дампы `docs/PLAN_v38_AI_MEGA.txt` (11 МБ),
  `docs/PLAN_v39/**` (1017 файлов, 37 МБ), `STEP_STATUS` (144), `LICENSES`, `WIKI`,
  `REGRESS_v39`, `PLAN_v39_EXEC_REPORT`, `SESSION_LOG.md`.
- **P0 фикс:** `tools/readiness.py` переписан — устранён `SyntaxError` (f-string
  с `\|`) на Python ≤ 3.11, который ломал `--readiness`, CI-шаг `compileall` и
  три тест-модуля. Отчёт о лицензиях/плане убран: он жил только ради удалённых документов.
- **Legacy вырезан:** удалены `app/core/orchestrator_v8..v12_patch.py` вместе с
  `master_pipeline_v12`, `wizard_v12_integration`, `release_pack_v9`, `mastering_v9`
  и CLI-флагами `--legacy-off/--legacy-report`. `_stage_polish` теперь одна
  каноническая ветка: `anti_neuro` → `anti_ai_polish` → честная копия.
- **Мёртвый код:** удалены 15 модулей без единой статической ссылки
  (`training_texts`, `cover_gen`, `model_manager`, `wizard_v8_extensions`, `beat_gen`,
  `phonk_engine_v2`, `musical_intelligence`, `genre_expansion_100`,
  `global_audit_fixer`, `provenance`, `ui/tutorial`, `ab_compare`, `lazy_dirs_patch`,
  `p0_truth_test`, `populate_cover_prompts`, `validate_final_track`, `plan_integrity`,
  `regress_v39`, `release_preflight`, `deep_audit_v40*`).
- **Имена без версий:** `*_vN.py` переименованы в канонические
  (`anti_neuro`, `llm`, `lyric_vault`, `voice_vault`, `rvc_trainer`, `tiktok_edit`,
  `video_edit`, `distribution`, `expert_mode`, `health`, `kpi_dashboard`, `kpi_monitor`,
  `self_diag`, `onboarding`, `theme`, `tools/e2e`, `tools/smoke_audio`, `tools/smoke_god`).
- **Данные и состояние:** пользовательское состояние убрано из git
  (`lyric_vault/*`, `voice_vault/*`, `data/hw_profile.json`, `data/tutorial_settings.json`,
  `training_texts/progress.json`, `data/kpi_history_seed`); `.gitignore` переписан на
  allowlist вместо глоба `*.json`.
- **Скрипты запуска:** 6 корневых bat/sh/ps1 сведены в `scripts/` (`setup.cmd`,
  `run.cmd`, `verify.cmd`, `make_shortcut.ps1`, `run.sh`).
- **Документация:** `README.md` переписан, добавлены `docs/ARCHITECTURE.md` и
  `docs/WORKFLOW.md`, `PROJECT_STATE.md` генерируется из `tools/readiness.py`.
- **Проверки:** `compileall` = 0 ошибок, `pytest tests/` = **287 passed**,
  `smoke_audio` = 6/6, `smoke_god` = 8/8, `--readiness` = 65 % (ограничения честные:
  нет `.pth` RVC, MusicGen/Demucs, микрофона в CI).


## v39.9.0 — финализация всех 100 primary шагов PLAN_v39

- **Приватность и offline-first:** KPI history сохраняет только allowlisted non-PII metrics; Freesound, GitHub-status и update URL calls требуют явного opt-in (`--online` или `network.online=true`).
- **Проверяемые runtime paths:** `--legacy-off` печатает compatibility matrix без импорта патчей; `--ai` отображает 12 real stage updates (duration/VRAM/status); классический CPU pipeline возвращает валидный `master_path` без Torch.
- **Поставка:** `python -m build` создаёт installable wheel с `zs-music-maker`; чистый venv выполняет установленный `--version`. Release preflight проверяет main, source-version mirror, console entrypoint и доступность source-implied tag.
- **Evidence:** execution report извлекает commit evidence for all primary headings; plan integrity verifies strict UTF-8, exact 001–100 headings and SHA-256. Final local acceptance completed with 237 pytest tests, compileall, AST audit and managed-data audit.
- **Ограничение:** MusicGen, SDXL, XTTS, RVC, Demucs, CLAP and LLM model runtime/weights are optional. Their absence is reported as BLOCKED/fallback; this release does not claim local heavy-model inference.


## v39.9 — PLAN_v39 ШАГИ 023–068 (AI pipeline, safety, release, docs)

- **AI pipeline:** роли, quality gates, dossier, lyrics/beat/vocal/cover/master adapters, secure manifest и deterministic fallbacks расширены последовательными контрактами и regression tests.
- **Операции:** очередь рендера, release fingerprints/ZIP, hit-score cache, explicit internal AI-risk heuristic, secure installer/update status/path redaction.
- **Supply chain:** model pull/verify сохраняет role-scoped artifacts и проверяет published checksums; data inventory остаётся 73 managed / 0 unknown / 0 invalid.
- **CI/CD:** Windows PyInstaller workflow сохраняет EXE artifact 30 дней; `v*` tag после успешной build публикует GitHub Release с ZIP.
- **Документация:** README/INSTALL/DEVELOPER_GUIDE синхронизированы с реальными v39 CLI contracts. На приёмке документации: 137 pytest PASS, AST dead-imports 0.
- **Ограничение:** runtime для тяжёлых optional packages и model weights остаётся environment-dependent и при отсутствии честно BLOCKED.


## v39.9 — PLAN_v39 ШАГИ 018–022 (metadata + audio quality gates)

- **ШАГ 018:** analysis_llm применяет общий schema-validator для трековых и агрегированных досье; неполные структуры фиксируются как честный rejected/deferred result.
- **ШАГИ 019–020:** metadata-стадия формирует и сохраняет валидный `metadata.json` даже без LLM, используя прозрачный deterministic fallback. Валидация проверяет title, описание и непустые теги.
- **ШАГИ 021–022:** добавлены метрики audio artifact (читаемость, длительность, sample rate, каналы, peak, RMS). И MusicGen, и CyberSynth fallback проходят gate до выставления `ok=True`; silent, missing и слишком короткий файл блокируются с reason.
- **Покрытие:** добавлены регрессии metadata-контракта, signal/silence audio quality и dry-run fallback; тяжёлые модели остаются BLOCKED до явного pull/install.


## v39.8 — PLAN_v39 ШАГИ 013–017 (data inventory + LLM quality)

- **ШАГ 013:** `tools/audit_data_inventory.py` читает и валидирует каждый versioned asset из `data/`; добавлены тесты чистого каталога и диагностики неизвестного/битого файла. Инвентарь: 73 managed, 0 unknown, 0 invalid.
- **ШАГ 014:** удалён устаревший reference-cache JSON, сохранён `.gitkeep`; `.gitignore` защищает локальные `reference_cache`, KPI/history, profile, secrets и API-key от случайного коммита. Сжатый архив HEAD — около 1.0 MB, tracked audio/model binaries отсутствуют.
- **ШАГИ 015–016:** `lyrics_llm` использует общий валидатор длины, токенов и повторяемости; invalid output запускает существующий fallback до записи `lyrics.txt`. Метрики прикладываются к результату стадии.
- **ШАГ 017:** output analysis_llm в artist dossier и track dossier проходит schema-валидацию; неполный JSON становится честным deferred/error результатом. Обе LLM-роли остаются BLOCKED без весов и `llama_cpp`, а не заявляются как установленные.


## v39.7 — PLAN_v39 ШАГ 012 (legacy isolation + God Mode checkpoints)

- **ШАГ 012:** добавлен `--legacy-off`, отключающий импорт и регистрацию legacy-патчей v8–v12 для runtime-пайплайнов без удаления совместимого Wizard-слоя.
- **Наблюдаемость legacy:** loader возвращает отчёт `enabled/loaded/skipped`; успешный вызов `anti_neuro` в core-оркестраторе получает `stage_marker=LEGACY`, а fallback сохраняет `legacy_attempt`.
- **FIX P0 God Mode:** `ZSPipeline` поддерживает явный `checkpoint_dir`. `run_god_pipeline()` изолирует checkpoints в собственном `out_root` и не переиспользует их для smoke/изолированных запусков. Устранён false-completed результат с отсутствующим `master_god.wav` после очистки out_root.
- **Покрытие:** добавлены четыре регрессионных теста — безимпортный legacy-off, CLI wiring, LEGACY marker и explicit checkpoint directory.
- **Приёмка:** 53 pytest PASS, AST dead-imports = 0, smoke_audio = 6/6, smoke_god = 8/8, `--legacy-off --smoke` = 8/8, fallback audit = 0 red flags.


## v39.6 — PLAN_v39 ШАГ 011 (import-cycle guard + audio regression)

- **ШАГ 011:** `tests/test_ai_layer.py` теперь строит статический AST-граф прямых импортов `app.core`, `modules` и `agents`, запрещая циклы с полным путём диагностики. Lazy-imports внутри функций намеренно исключены.
- **Регрессия детектора:** добавлен искусственный трёхузловой цикл, подтверждающий корректность обнаружения; фактический граф проекта — 104 модуля, 18 рёбер, 0 циклов.
- **FIX P0 audio:** `modules/beat_constructor.py` заменяет односторонний Haas-mix на контролируемое mid/side-расширение. Исправлен реальный `smoke_audio` fail: beat correlation 0.842, проверка 6/6 PASS.
- **Покрытие:** добавлен детерминированный тест стереоширины конструктора бита; тест проверки `essentia` больше не зависит от случайного состава необязательных локальных пакетов.
- **Приёмка:** 49 pytest PASS, AST dead-imports = 0, smoke_audio = 6/6, smoke_god = 8/8, fallback audit = 0 red flags.


## v39.5 — PLAN_v39 ШАГИ 006-010 (deps, config, CI, version, AST)

- ШАГ 006: requirements выверены по AST-графу импортов; +cryptography, audiomentations, moviepy(<2), noisereduce, lyricsgenius, mingus; AI-стек +essentia, pyAudioAnalysis, bark(git), rvc-python; pyproject deps синхронизированы, добавлен [project.optional-dependencies.ai].
- ШАГ 007: config/settings.py — единые настройки (.env → env → дефолты), подключены в main.py --version и orchestrator_ai.
- ШАГ 008: CI +job audit (compileall, AST dead-imports, pytest, --version).
- ШАГ 009: version.json — единственный источник версии; pyproject dynamic через app/version_info.py; тест сверки.
- ШАГ 010: tools/ast_dead_imports.py + чистка: musical_intelligence, orchestrator_god, genre_validator, test_ai_layer, ui/__init__; аудит = 0.

## v36 — 2026-08-14 (session-docs-unification-silent-except-build-fixes)

- **FIX P1 README/CHANGELOG unification** — вычищены протухшие блоки «Что нового в v14/v17/v18», ссылки на удалённые smoke_v14/v15/v17/v18/v21/v24/v25 (перенесены в `docs/legacy/` ещё в v29). Таблица статусов и раздел «Тесты» приведены к текущему v35+ ядру.
- **FIX P1 `main.py --smoke`** — fallback-цепочка чистилась от мёртвых имён (`tools.smoke_v14/v15/v17/v21/v24/v25`). Оставлены только реально работающие `tools.smoke_god` → `tools.smoke_audio`. Больше не спамит 6 строк «failed: No module named».
- **FIX P2 silent-except в критичных путях:**
  - `app/plugins/base.py:48` — `except: pass` внутри Sanitize-warning: теперь честно логирует в stderr, если `app_logger` недоступен.
  - `app/core/cover_gen.py:39` — `except: continue` в font-loop разделён на штатный `OSError` (шумовое отсутствие шрифта) и общий `Exception` с записью в stderr.
- **FIX P1 `.github/workflows/build.yml` (PyInstaller EXE)** — добавлены `--add-data models`, `--collect-submodules modules|app|agents|tools|ui|updater` вместо мёртвого `--hidden-import modules`. Smoke-шаг больше НЕ `continue-on-error: true` — падение EXE теперь ломает сборку (раньше «зелёная» сборка выпускала мёртвый EXE).
- **Cleanup `requirements.txt`** — убран устаревший заголовок «v10 Chart Killer Pro» и упоминание несуществующего `windows_build.bat`. Опциональные тяжёлые пакеты вынесены отдельной секцией с указанием на INSTALL.md §4.
- **Docs sync** — `INSTALL.md`, `PROJECT_STATE.md`, `version.json`, `pyproject.toml` подняты до v36.0.0.

## v35 — 2026-08-14 (session-silero-real-musicgen-status-cleanup)

- **REAL_PASS: `voice_synth` Silero TTS** — впервые подтверждён реальным прогоном на CPU (RU v3.1, female=kseniya, WAV 48kHz/6.7s живой сигнал). Статус снят с FALLBACK_ONLY.
- **FIX P1: `musicgen_texture`** — добавлен honest `detect_availability()`/`get_status()` (проверка torch+audiocraft БЕЗ загрузки весов) вместо молчаливого падения в лог; лог причины BLOCKED на вызове.
- **FIX P2: точечная честность silent except** — `master_pipeline_v12` (log-write/progress_cb/hit_scorer) и `release_pack_full` (ID3-обложка) больше не проглатывают ошибки молча — честно логируют в stderr/лог.
- **Cleanup:** удалён мёртвый `safe_import.py` (0 продакт-импортов); из git-индекса убраны чужие снапшоты `data/health.json`/`data/kpi_dashboard.json`; `tutorial_settings.json` перенесён в `data/` (дубль после миграции v34).
- **FIX INSTALL.md:** зафиксирована согласованная пара `torch==2.5.1`+`torchaudio==2.5.1` с pytorch-индекса (реальный ABI-баг: PyPI-torchaudio несовместим с torch pytorch-индекса → `_torchaudio.abi3.so` не грузится) + проверенный Silero-путь (`omegaconf soundfile`).

## v34 — 2026-08-13 (session-backlog-fixes)

- FIX P2: `app/core/model_manager` — lazy torch import (core-слой больше не падает без torch).
- FIX P2: license-gate реально подключён к `sample_hunter_v9.search_online()` + нормализация URL-лицензий в `license_manager`.
- FIX P3: `voice_onboarding.run_cli()` возвращает 0/1 по capability микрофона.
- FIX P3: `tutorial_settings.json` — единый путь `data/tutorial_settings.json` для `onboarding` и `ui/tutorial`.
- FIX P3: `voice_synth.synth(gender=...)` (male=aidar / female=kseniya).
- FIX P2: `_json_safe()` в `orchestrator_god.meta` (numpy-скаляры больше не превращаются в `np.float32(0.95)` строки).
- FIX main.py: валидация `--genre` против StyleRegistry с difflib-подсказкой (rc=2 + suggest).
- Docs sync: version 34.0.0 в version.json/pyproject/README/PROJECT_STATE.
- `.env.example` создан на основе реального сканирования кода.

## v33 — 2026-08-13 (session-full-pass)

- FIX P0: `run_all_smoke.bat` (4 несуществующих smoke) → прогон `tools/smoke_v*.py`.
- FIX P0: `voice_synth` уникализация draft-имени timestamp'ом (нет коллизий).
- FIX P0: `orchestrator_god` больше не режет вокал до 200 символов (safety-cap 4000).
- FIX P0: INSTALL.md переписан (убраны ссылки на несуществующий windows_build.bat, gradio-порт).
- FIX P1: unification версий 33.0.0 (version.json / pyproject / README / PROJECT_STATE).
- FIX P1: numpy пин `<2.0` снят (совместимость с 2.4.x подтверждена).
- FIX P1: `install.py` — `shell=True` убран.
- FIX P1: `async-mode` возвращает 1 при падении пайплайна.
- FIX P1: CI прогоняет smoke_audio + smoke_god + fallback_audit + CLI-sanity (раньше только 7 pytest).
- FIX P1: launcher cleanup (удалены дубли run_v8/v9/v11.bat и run_v14.sh в docs/legacy/).
- NEW: `tools/fallback_audit.py` теперь ловит многострочные вызовы с маркером `ZSMM_NOT_RVC` (red_flags=0).

## v30–v32 — audit + restore + God Mode E2E

- v30: восстановлены 5 ошибочно удалённых модулей (lyrics_gen_v8, mastering_v9, release_pack_v9, kpi_monitor, lyric_vault); `voice_synth` honest-empty-return; создан `run.bat`; `verify.bat` переписан на реальные тесты.
- v31/v32: два глубоких аудита без правок — 46 находок в SESSION_LOG (INSTALL.md битый, health-RED из-за опциональных heavy-deps, рассинхрон версий, ложные red-флаги, архитектурный распад оркестраторов).

## v29 — God Mode E2E + true-peak mastering

- FIX P0: `midi_generator.generate_melody_pattern` guard без mido (honest BLOCKED).
- FIX P1: `mastering_pro` true-peak -1 dBTP, NaN/Inf-guard, mono→stereo, honest output metrics.
- NEW: `tools/smoke_god.py` (God Mode E2E → master_god.wav) 8/8 PASS.
- Cleanup: 11 устаревших smoke → docs/legacy/.

## v28 — cleanup + God Mode wizard fix + CI

- Репо очищено от 72 output-артефактов (~262MB), `.gitignore` расширен.
- God Mode `wizard_state=None` защищён Optional + default.
- Добавлен `.github/workflows/build.yml` (Windows EXE, PyInstaller).
- Создан SESSION_LOG.md.

## v27 и раньше

Полная история — в `SESSION_LOG.md` (архивная секция).

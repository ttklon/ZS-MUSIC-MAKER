# WORKFLOW — как менять проект

> Правила, которые не дают коду снова превратиться в набор версий.

Устройство кода — `docs/ARCHITECTURE.md`; что где лежит и в каком состоянии —
`docs/PROJECT_INVENTORY.md`. Этот файл — про процесс, не про состав.

## Базовый цикл

```bash
python -m pytest tests/ -q          # должно быть зелёно ДО и ПОСЛЕ изменения
python tools/smoke_audio.py         # аудио-гейты
python tools/fallback_audit.py      # честность fallback
python tools/ast_dead_imports.py    # мёртвые импорты
python main.py --run --seed 42 --only beat,lyrics   # воспроизводимый частичный прогон
```

Коммит = одно логическое изменение + обновлённый `CHANGELOG.md`.
Никаких новых файлов вида `*_v2.py`, `*_final.py`, `*_new.py` — правь существующий модуль.

## Добавить жанр

Каталог жанров один: `config/genres_100.json` — 6 категорий по 20 названий.
Пресеты для генерации — `data/genre_presets/` (`<slug>.json`) (50 файлов):
`bpm`, `mode`, `groove` (16/32 шага по слоям), `prompt_hint`, `instruments`,
`mix` (уровни), `mastering` (целевой LUFS). Каталога `data/genres/` нет.

1. Добавь имя в подходящую категорию `config/genres_100.json` (без дублей: `trap`
   и `grime` уже встречаются в двух категориях).
2. Пресет — `data/genre_presets/` (`<slug>.json`).
3. `python tools/genre_validator.py` — схема и уникальность.
4. `python main.py --list-genres` — жанр виден в CLI.

## Добавить стадию в пайплайн

1. Функция `_stage_<name>(...) -> dict` в `app/core/stages/<тема>.py` (не в оркестраторе:
   там только склейка).
2. Возвращает `{ok, ...}`; при отказе — `{ok: False, reason: "...", blocked: True}`.
3. Артефакт обязан пройти валидатор из пакета `app/ai/quality/`.
4. Добавь стадию в `run_full_pipeline` и, если у неё есть ключ для `--only`,
   в `STAGE_KEYS` (`app/core/pipeline_runtime.py`); обнови `docs/ARCHITECTURE.md`.
5. Тест: успешный путь + отказ + детерминизм по seed.

## Добавить AI-роль

1. Спецификация в `app/ai/registry.py` (engine, upstream, файл, размер, SHA-256, VRAM).
2. Pull/verify в `tools/pull_ai_models.py`.
3. Адаптер в `modules/`, принимающий уже загруженный `handle` (никаких вложенных `use()`).
4. `AIStage(..., optional=True)` + безопасный fallback.
5. Fake-handle тест: контракт адаптера проверяется без имитации inference.

## Добавить сэмплы

1. Файлы в `data/samples/<категория>/`, запись в `data/samples/manifest.json`
   (`tools/import_samples.py` предназначен только для двух указанных в нём наборов, не для произвольных паков):
   `name, category, bpm_range, key, license, source, sha256`.
2. Лицензия обязательна: без неё сэмпл не попадает в релиз-пакет.
3. `python tools/audit_data_inventory.py` — проверка структуры.

## Правила качества

- Файл ≤ 400 строк; функция ≤ 60 строк — мягкое правило: существующие
  исключения перечислены в тесте гигиены, новые длинные функции не появляются.
- Ни одного `except: pass` — только логирование причины.
- Никакого фейкового успеха: нет весов/пакета → `BLOCKED` с причиной.
- Любой рендер воспроизводим по `seed`.

# WORKFLOW — как менять проект

> Правила, которые не дают коду снова превратиться в набор версий.

## Базовый цикл

```bash
python -m pytest tests/ -q          # должно быть зелёно ДО и ПОСЛЕ изменения
python tools/smoke_audio.py         # аудио-гейты
python tools/fallback_audit.py      # честность fallback
python tools/ast_dead_imports.py    # мёртвые импорты
```

Коммит = одно логическое изменение + обновлённый `CHANGELOG.md`.
Никаких новых файлов вида `*_v2.py`, `*_final.py`, `*_new.py` — правь существующий модуль.

## Добавить жанр

1. `data/genres/<slug>.json`: `bpm`, `mode`, `groove` (16/32 шага по слоям), `prompt_hint`,
   `instruments`, `mix` (уровни), `mastering` (целевой LUFS).
2. `python tools/genre_validator.py` — схема и уникальность.
3. `python main.py --list-genres` — жанр виден в CLI.

## Добавить стадию в пайплайн

1. Функция `_stage_<name>(...) -> dict` в `app/core/orchestrator.py` (или отдельный модуль,
   если стадия тяжёлая).
2. Возвращает `{ok, ...}`; при отказе — `{ok: False, reason: "...", blocked: True}`.
3. Артефакт обязан пройти валидатор из `app/ai/quality.py`.
4. Добавь стадию в `run_full_pipeline` и в таблицу `docs/ARCHITECTURE.md`.
5. Тест: успешный путь + отказ + детерминизм по seed.

## Добавить AI-роль

1. Спецификация в `app/ai/registry.py` (engine, upstream, файл, размер, SHA-256, VRAM).
2. Pull/verify в `tools/pull_ai_models.py`.
3. Адаптер в `modules/`, принимающий уже загруженный `handle` (никаких вложенных `use()`).
4. `AIStage(..., optional=True)` + безопасный fallback.
5. Fake-handle тест: контракт адаптера проверяется без имитации inference.

## Добавить сэмплы

1. Файлы в `data/samples/<категория>/`, запись в `data/samples/manifest.json`:
   `name, category, bpm_range, key, license, source, sha256`.
2. Лицензия обязательна: без неё сэмпл не попадает в релиз-пакет.
3. `python tools/audit_data_inventory.py` — проверка структуры.

## Правила качества

- Файл ≤ 400 строк, функция ≤ 60 строк.
- Ни одного `except: pass` — только логирование причины.
- Никакого фейкового успеха: нет весов/пакета → `BLOCKED` с причиной.
- Любой рендер воспроизводим по `seed`.

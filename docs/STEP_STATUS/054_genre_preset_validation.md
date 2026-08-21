# PLAN_v39 — ШАГ 054: валидация preset genres

`tools/genre_validator.py` переписан как два независимых аудита. `validate_preset_assets()` проверяет именно **50 versioned JSON** в `data/genre_presets` по фактической schema проекта: genre, BPM range, keys, structure templates, mood tags, vocal style и mastering profile. `validate_runtime_genres()` дополнительно проверяет все **119** profiles, доступные через `StyleRegistry`/`GenreFactory`.

Фактический запуск выводит `Preset assets: 50/50`, `Runtime genres: 119`, `PASS`. Это устраняет прежнее несоответствие: старый validator сообщал только о «119+ жанрах» и не подтверждал целостность 50 versioned assets.

На момент приёмки: `python tools/genre_validator.py` — успешно; полный `pytest tests/ -q` — **119 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**.

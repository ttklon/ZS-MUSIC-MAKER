# Data catalog

Каталог `data/` содержит только **versioned seed-данные, fixtures и переносимые настройки**, необходимые для воспроизводимых проверок и безопасного запуска проекта. Проверка `python tools/audit_data_inventory.py` читает каждый файл каталога, валидирует его формат и не допускает неизвестные активы.

| Путь | Назначение | Правило жизненного цикла |
|---|---|---|
| `genre_presets/` | Каталог переносимых профилей жанров. | Versioned JSON seeds; загружаются по glob реестром жанров. |
| `prompts/` | Текстовые шаблоны AI-промптов. | Versioned UTF-8 assets. |
| `kpi_history_seed/` | Валидные примеры истории KPI. | Versioned JSONL fixture; рабочая история игнорируется. |
| `sample_manifests/` | Воспроизводимые manifest-fixtures. | Versioned JSON fixtures; online-кэш не хранится в Git. |
| `reference_cache/` | Пустой каталог для локального кэша анализа референсов. | Все runtime JSON игнорируются; в Git сохраняется только `.gitkeep`. |
| `tutorial_settings.json` | Стартовая настройка onboarding. | Versioned JSON seed. |
| `hw_profile.json` | Пример аппаратного профиля. | Versioned JSON seed; runtime-snapshot игнорируется. |

> Никогда не добавляйте в Git пользовательские ключи, шифрованные secrets, историю треков, runtime-кэш или результаты анализа. Для проверки перед коммитом запускайте `python tools/audit_data_inventory.py`.

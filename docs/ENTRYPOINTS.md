# Карта точек запуска и политика поддержки

> Политика: основной продукт — Electron. Ни один legacy-вход не принят как замена основной студии.

| ID | Команда | Исходник | Политика |
|---|---|---|---|
| electron | `ZS Music Maker.exe` | `desktop/electron/main.js` | primary_development |
| python_default | `python main.py` | `main.py` | redirect_instructions_only |
| python_cli | `python main.py --help` | `app/cli` | engineering_not_product_acceptance |
| installed_cli | `zs-music-maker --help` | `pyproject.toml` | engineering_not_product_acceptance |
| pyside | `python main.py --desktop` | `app/gui` | legacy_not_supported_as_product |
| gradio | `python main.py --gradio` | `app/cli/gui.py` | legacy_not_supported_as_product |
| console | `python main.py --console` | `app/cli/commands.py` | legacy_not_supported_as_product |
| hitmaker | `python hitmaker.py` | `hitmaker.py` | experimental_not_supported_as_product |
| karaoke | `python -m ui.karaoke_recorder` | `ui/karaoke_recorder.py` | engineering_diagnostic_not_product |
| pyside_onboarding_demo | `python -m app.gui.onboarding` | `app/gui/onboarding.py` | developer_demo_not_product |
| pyside_theme_demo | `python -m app.gui.theme` | `app/gui/theme.py` | developer_demo_not_product |
| preview | `npm run preview` | `desktop/scripts/preview-server.js` | developer_mock_bridge_only |
| cmd_launchers | `scripts/run.cmd; scripts/run_silent.cmd` | `scripts` | legacy_not_supported_as_product |

## Поведение

- `python main.py` без режима печатает ссылку на основной установщик и завершается с кодом 2.
- Не запускаются PySide/Gradio/REPL по очереди; не выполняется неявная подготовка перед read-only командами.
- `--desktop`, `--gradio`, `--console` сохранены для явного инженерного выбора с предупреждением LEGACY.
- `hitmaker.py` помечен как экспериментальный; это не обещание хита и не основной launcher.
- Python CLI, God/AI/async, hit-factory и flags доступны как инженерные режимы, без продуктовой приёмки. Их контракты мигрируют отдельно.
- Демо theme/onboarding, karaoke diagnostic и browser preview не являются пользовательскими точками создания песни.
- Старые cmd-лаунчеры явно предупреждают о legacy; run_silent по-прежнему использует pythonw при явном выборе старого мастера.
- Главный установленный Electron EXE и его portable-вариант — один продукт; npm start — запуск того же окна для разработки.

## Проверка

`python main.py --entrypoints` читает реестр без скачивания.
`python main.py --help` и `--version` остаются доступными. Реальное окно проверяется Windows packaged job.

Политика legacy означает отсутствие поддержки как основного продукта, а не утверждение, что каждая инженерная команда уже испытана.
Удаление старых входов не требуется для совместимости; обратного автоматического fallback нет.
При ошибке: сохранить журнал, открыть установленный продукт. Не устанавливать GUI-пакеты ради открытия другого мастера.

Источник политики: `app/core/entrypoints.py`. Регрессии: `tests/test_product_maps.py`.

# PLAN_v39 — ШАГ 051: GUI AI status и pipeline entry

В PySide wizard добавлена отдельная страница **AI: модели и pipeline**. Она получает данные непосредственно из `ModelRegistry.status()` и `MODEL_REGISTRY`, отображая для каждой из 13 ролей engine, назначение, оценку VRAM и состояние `READY` либо `NO MODEL/DEPENDENCY`. Проверка availability не загружает веса в VRAM и обновляется по таймеру раз в пять секунд или по кнопке.

Страница доступна и как первый экран wizard, и через меню **AI → Статус моделей**. В верхней строке показаны текущая загруженная роль, VRAM/RAM budget и CPU threads; это делает sequential-ограничение модели наблюдаемым в GUI, а не только через CLI report.

На момент приёмки: `compileall app/gui/wizard.py app/ai/registry.py` — успешно; `pytest tests/ -q` — **116 passed**; AST-аудит — **0 dead imports**. PySide6 GUI не запускается в headless sandbox, поэтому визуальная интерактивная проверка здесь честно не заявляется; страница проверена синтаксически и использует только существующий public registry API.

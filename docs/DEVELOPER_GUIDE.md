# ZS Music Maker — руководство разработчика

## Базовый рабочий цикл

Работайте в `main` только с небольшими проверяемыми изменениями. Перед коммитом выполните `python -m pytest tests/ -q`, `python -m compileall -q app agents modules tools updater ui main.py` и `python tools/ast_dead_imports.py`. Для каждого планового шага добавляйте отчёт в `docs/STEP_STATUS/` и запись в `SESSION_LOG.md`.

> Heavy AI dependency или веса, отсутствующие в среде, должны давать **BLOCKED**, `skipped` либо проверенный fallback. Не маркируйте fake handle/unit test как реальный inference.

## Добавление AI роли

1. Добавьте спецификацию в `app/ai/registry.py`: key, engine, upstream source, file, оценку VRAM/RAM и loader.
2. Добавьте pull manifest behavior в `tools/pull_ai_models.py`. Downloadable weight должен быть проверяемым по size/SHA-256, когда upstream публикует эти данные.
3. Добавьте отдельный adapter в `modules/`, принимающий уже загруженный `handle`. Не выполняйте вложенный `registry.use()` внутри stage.
4. Зарегистрируйте `AIStage` в `app/core/orchestrator_ai.py`; heavy stage должен быть `optional=True` и иметь безопасный fallback/skip reason.
5. Добавьте fake-handle regression. Проверяйте контракт adapter-а, но не имитируйте успешное heavy inference.

## Стадии и качество

`SequentialAIRunner` последовательно держит одну роль в памяти, освобождает handle в `finally`, собирает timeout/VRAM telemetry и применяет OOM ceiling. Каждая стадия возвращает структурированный dict. Artifact, который передаётся следующей стадии, должен пройти соответствующий validator из `app/ai/quality.py`.

| Артефакт | Валидатор |
|---|---|
| Текст | `validate_song_lyrics` |
| Мастер | `validate_master_artifact` |
| Обложка | `validate_cover_artifact` |
| Stem/ASR/tags/DSP | специфичные validators из `app.ai.quality` |

## Сессии, пути и безопасность

AI run сохраняет `manifest.json` schema v1. Новые runtime outputs не добавляйте в versioned fixtures. Для identifiers и paths используйте `safe_identifier`/`safe_child_path`; сообщения, содержащие внешние ошибки или credentials, пропускайте через central logger, который выполняет redaction.

## Документация и release

Обновляйте README только командами, которые действительно существуют. `python main.py --update` является read-only status check; он не применяет обновление. Tagged `v*` build workflow публикует Windows artifact release после успешной CI build; не создавайте tags без завершённой release приёмки.

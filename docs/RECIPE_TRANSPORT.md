# Рецепт, единый слот исполнения и события (T0101–T0130)

## Разрыв и границы

Baseline до этой порции: `_run_pipeline` агента передавал `make_one` только
жанр, тему и длительность, теряя подготовленные текст/голос/референсы/BPM.
`reference_lyrics` в lyrics stage — контекст, а не точный текст для исполнения.
Само наличие этих полей в плане не доказывало, что они используются.

Теперь агент передаёт **полный plan как recipe**, `evolve=False`: явные параметры
не меняются повторной эволюцией. Успешный текст агента попадает также в
`user_lyrics_lines`; реальная lyrics stage использует эти строки без нового LLM. Историческое имя provider=user_lyrics означает готовые строки,
а не подтверждение авторства пользователя: источник агента остаётся в его отчёте.
При успешно выполненном prepare_voice/RVC `use_rvc=False`, чтобы повторно не
конвертировать уже обработанный дубль. Это не проверка качества или прав голоса.

## Канонический вход и совместимость

Используется существующий `snapshot_recipe`/`restore_recipe`, version=1, JSON
round trip, ограничение 1 MiB и запрет неизвестных верхнеуровневых полей.
Новый `HitFactory.make_one(recipe=...)` не смешивается с legacy kwargs.
Recipe содержит genre/theme, duration_sec, seed, bpm_override, artist,
references, own_vocal_wav/use_rvc, reference_lyrics/user_lyrics_lines, style_vector
и остальные известные поля. Явный API проверяет типы чисел/строк/списков/флагов.
None для seed/BPM/duration/aggression означает auto; разрешённое фактическое
значение остаётся в wizard_state и snapshot. Seed=0 и False не теряются.

Пример: `make_one(recipe={"genre":"trap", "theme":"Ночь", "seed":123,
"duration_sec":37, "bpm_override":143, "references":["ref.wav"],
"own_vocal_wav":"take.wav", "use_rvc":false}, evolve=False)`.
Ожидание на границе executor: те же явные значения; неизвестный ключ/NaN/
двусмысленный тип отвергается до аудиопрогона. Legacy kwargs остаются совместимы.
Стилевой вектор сохраняется в snapshot; приоритет resolver: preset → переданный
style_vector → актуальный analysis → явный BPM; seed задаёт рецепт.

Это **не** доказательство всех стадий и нового UI: основной мастер пока принимает
только тему/ориентир, явный выбор длины/seed/своего голоса не подключён.
T0109/T0110 заблокированы до полного UI→stage→reopen/export протокола.

## Исполнитель

`registerTaskIpc` использует общий `state.taskSlot` capacity=1, включая await
подготовки workspace. Повторный старт возвращает явный busy с taskId текущей
задачи; скрытой очереди скачиваний нет. Даже два registration с одним state не
могут параллельно готовить workspace. Ошибка подготовки освобождает слот,
повтор допускается. Нативные операции используют тот же вход и получают ID.

Каждый принятый запуск получает UUID: reply.data.taskId, task-event/task-done
имеют taskId/eventVersion=1, Python получает ZSMM_TASK_ID. Прямой CLI генерирует
ID самостоятельно. Это корреляция, не авторизация. Создание в UI буферизует
события до ответа запуска и затем принимает только ID своей задачи.

Ограничения: это не межпроцессный файловый lock и не защита от отдельного CLI.
Не все отдельные IPC установки/записи/beat-service включены в слот. Отмена в
подготовке и дерево процессов требуют следующего пакета; T0119/T0120 blocked.
`pipeline_runtime._apply_seed` остаётся каноническим применением seed к стадиям.

## NDJSON v1

Одна строка — JSON: schema="zsmm.task", version=1, task_id, seq начиная с 1,
type progress/artifact/error/done. Progress/error имеют message; artifact —
role/path; done — ok:boolean и report:object. Terminal единственный. Встроенные
переносы экранируются JSON. Артефакт сам по себе не значит success/quality accepted.

Обычные stdout/stderr остаются журналом. Поиск JSON-подстроки с master_path
удалён из creation/agent/agent-service. `task-stream` собирает UTF-8 по чанкам,
CRLF/EOF, ограничивает строку 1 MiB, отклоняет ID/seq/version/двойной terminal.
После превышения лимита восстанавливает границу строк, но весь результат уже
не может стать успешным. Для agent-hit exit 0 без принятого terminal недостаточен;
нужны terminal.ok, canonical result.succeeded/status=success, отсутствие protocol
errors и успешный exit. UI не объявляет complete после ошибочного завершения.

Позитивные и негативные тесты используют двойники дорогого executor и реальный
маленький Python subprocess, не модель/пение. Bootstrap пока остаётся обычным
логом. Полный installed-app маршрут с реальным backend/ошибкой/отменой ещё не
принят: T0129/T0130 blocked. Структура events не является подписью backend.

## Проверка и откат

`pytest tests/test_recipe_transport.py tests/test_recipe_contract.py
 tests/test_agent_guide.py`; Node task-stream/tasks/task-runner/creation tests.
Windows workflow product-plan проверяет эти границы и packaged navigation;
это не clean NSIS, микрофон или генерация песни. Отказ gate публикации сохраняется.
Откат — revert кода/документации; никаких проектов, моделей и release assets
не удалять. Старый опубликованный v42.0.39 не получает изменения автоматически.

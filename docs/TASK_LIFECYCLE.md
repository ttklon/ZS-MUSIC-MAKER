# Жизненный цикл задач, отмена, каталоги и диагностика (T0131–T0180)

Порция по новому правилу пользователя: **50 пунктов**, пять исходных пакетов.
Это изменения development, не новый installer. Установки моделей/NSIS и реальное
пение не заменяются числом тестов. Непринятые проверки остаются blocked.

## Подготовка и генерация

Baseline: creation переходил к генерации при `bootstrap` exit 0; структура setup
не проверялась. Код 0, readiness percentage и отсутствие исключения — не
доказательства всех движков. Даже `{heavy:{},models:{}}` теперь не проходит.

Канонический автомат `core/creation-state.js`: idle → preparing → ready/blocked,
ready → running → done/blocked. Попытка generation без принятого setup блокируется
и обработчиком запуска, и disabled-кнопкой; ручная навигация это не обходит.
Bootstrap CLI выдаёт NDJSON done с report.setup (schema=1, ok, blockers,
inference_verified=false). tasks.js требует terminal setup, не только exit.
Ready означает принятую структуру отчёта подготовки, **не inference или пение**.
Проверка действительных моделей и их coverage по всем ролям остаётся отдельной.

## Остановка и подтверждение

Baseline: `child.kill()` останавливал только корневой Python. Теперь POSIX child
имеет отдельную process group; отмена/total-timeout посылают группе SIGKILL.
Windows использует `taskkill.exe /PID <числовой pid> /T /F` без shell. Пользователь
видит stopping; ответ stop означает **запрос**, окончательный task-done приходит
после child.close и результата команды termination. canceled и timedOut различны;
ни один не допускает ok=true даже при exit 0.

`termination.confirmed` означает успешную команду остановки группы/дерева плюс
последующий close корневого процесса. Это не постоянный системный Job Object и
не универсальная проверка каждого detached descendant. При неуспешной команде
результат не считается принятым cleanup, taskSlot сохраняется заблокированным.
В таком случае сохранить диагностику и проверить процессы; не запускать новую
установку автоматически. Рестарт приложения не является доказательством cleanup.

Во время prepareWorkspace stop подаёт AbortSignal; копирование проверяет его на
границах файлов, слот держится до settle. Отмена не выдаётся за мгновенный abort
системного copyFile; после неё Python не запускается. Частично скопированный код
не удаляется: следующий явный retry освежает код, не трогая модели/проекты.

Реальная regression: Python → Python grandchild держит файл (Windows byte lock),
cancel и timeout завершают его, PID больше не исполняется, следующий Python
повторно захватывает lock. Это не полный прогон pip/всех модельных workers.
Гонки исчезновения родителя/detached descendants требуют Job Object/дополнительных
проверок. T0149/T0150 не закрываются одним этим fixture.

## Время и активность

Отдельные сигналы:
- total hard deadline берётся из task catalogue (существующие лимиты задач);
- heartbeat раз в 5 секунд: elapsed/silence, **не процент/прогресс модели**;
- 60 секунд без вывода: предупреждение, не автоматическое убийство CPU;
- stage_activity раз в 15 секунд сообщает liveness текущей AI стадии без inputs.

Остановка monitor/thread в finally/close/error проверяется тестами. Стадийный
watchdog sequential_runner на Windows по-прежнему не может безопасно прервать
чужой native/Python thread до возврата; parent hard deadline завершает всю задачу.
Не называем этот marker полноценным Windows stage isolation. T0159/T0160 blocked.

## Каталоги и права

Install/resources — источник кода только для чтения. Для packaged задач CWD —
userData/workspace. Его output/models/cache/temp/logs отделены от python-packages
и встроенного .python. TMP/TEMP/TMPDIR, HF_HOME, TORCH_HOME, ZSMM_LOG_DIR и
ZSMM_WORKSPACE задаются для дочернего процесса; настройки пользователя не правятся.
Каждый runtime каталог проверяется реальной записью/удалением уникального probe.
Dev-запуск в репозитории сохранён для совместимости, не обещан как installed layout.

Workspace не может совпадать, быть внутри или **предком** install. Проверяются
symlink/junction в существующих предках путей и в источниках/назначениях файлов.
Нельзя вести code copy через junction в чужой каталог. Нет claims об устранении
TOCTOU на злонамеренно изменяемой FS; весь code tree пока не обновляется одной
атомарной транзакцией. Defaults seed-only, models/output не копируются/не удаляются.
Тесты проверяют сохранение исходников/моделей/проектов, отмену, junction, retry и
CWD subprocess. Чистой NSIS под обычным пользователем и всей матрицы ACL/дисков
ещё нет — T0169/T0170 blocked. Hosted runner не заменяет такую приёмку.

## Корреляция и диагностический экспорт

Task-runner пишет в локальный bounded startup-errors.jsonl только whitelist
lifecycle: taskId/key/type/code/outcome. **Не** argv, prompt, stdout/stderr,
settings, raw report, audio или файлы проекта. Typed Python error и renderer error
связываются тем же ID; creation хранит lastTaskId для showError. Это correlation,
не доверие к renderer и не доказательство причинности всех legacy ошибок.

Redaction перед записью и при экспорте скрывает известные формы token/password/
api-key/Bearer, URL и распространённые локальные пути. Файл ротируется ~1 MiB,
экспорт ограничен двумя собственными файлами после save dialog, cancel не пишет.
Ссылки на файлы журнала не читаются. Отдельно Python logger получает validated
ZSMM_TASK_ID, redacts **formatted traceback**, пишет в заданный user log dir и не
использует install/output fallback при ZSMM_WORKSPACE. Python app.log намеренно
не выгружается в этот пакет автоматически: он может содержать creative/private data.

Свободный текст ошибок может содержать неизвестные секреты/личные данные, которые
regex не распознает. **Перед передачей пакета нужен просмотр человеком.** Исторические
логи и все сторонние логгеры не признаны безопасными. Полный audit и независимая
приёмка экспортов T0179/T0180 остаются blocked. Сеть для экспорта не используется.

## Откат и доказательства

Откат — revert кода. Не очищать проекты/кэши/веса/опубликованные assets.
Windows product-plan запускает реальные subprocess/lock tests и packaged window,
но не установку нейросетей. Протокол и SHA находятся в docs/plan/evidence.
T0139/T0140 остаются blocked до реальной приёмки частичной подготовки/восстановления
через установленный мастер. Остальные незакрытые задачи не исчезают из backlog.

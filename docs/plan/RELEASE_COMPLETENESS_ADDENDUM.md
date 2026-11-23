# Обязательное дополнение полноты выпуска

Это расширение, а не замена T0001–T1000. Старые ID/история сохраняются.
A-ID — дополнительные сквозные интеграционные задачи: выполняются при работе
со связанным T-пакетом, а не откладываются до конца как необязательные пожелания.
Все ниже **не приняты** этим документом. Существующие доказательства можно
использовать после проверки их применимости к актуальному release candidate.
Количество задач не гарантирует продукт: при новом обязательном разрыве добавь
следующий A-ID с явными входами, выходами, зависимостями и evidence.

## Учёт

Для каждого A-ID создай acceptance record: owner, source SHA, связанные T-ID,
требование, исполняемый сценарий, окружение, positive/negative/recovery результаты,
artifact hashes, ограничения, решение. Документ не является сертификатом.
Выполняй A-ID порциями до 10 рядом с активным основным пакетом; основная очередь
restart.json остаётся из 1000 исходных ID и не ломается этим приложением.
Финальная готовность требует одновременно завершённых T и A, а не одного счётчика.

## Дополнительные задачи

| ID | Работа и обязательный выход | Приёмка / зависимости |
|---|---|---|
| A0001 | Полный пофайловый аудит актуального репозитория с журналом чтения, типов и связей | Все авторские файлы учтены; текст целиком прочитан; binary/secret/generated исключения объяснены; не SHA вместо чтения |
| A0002 | Traceability всех обязательных пользовательских требований к T/A, entrypoints и evidence | Нет требования без owner, теста и решения; зависит от A0001 |
| A0003 | Единый канонический runtime path из установленного UI к shared recipe/Python | Реальный installed artifact, без checkout PATH/PYTHONPATH и dev server; относится к T0025 |
| A0004 | Hardware preflight в том же установленном пути | Unknown/insufficient RAM/VRAM/disk дают конкретный отказ до тяжёлой работы; recovery сохраняет прежние файлы; A0003 |
| A0005 | Полная измеренная матрица принимаемых backend/моделей/режимов | Для каждой заявленной конфигурации реальный протокол; actual device и отсутствие скрытого fallback; A0004, T0029 |
| A0006 | Общая отмена и cleanup всех реально используемых тяжёлых workers | По каждой стадии cancel/timeout/crash, нет сирот, последующий job успешен; процессы наблюдаются на Windows; A0003 |
| A0007 | Один end-to-end инструментальный recipe через установленный продукт | Запрос → стадии → typed result → playback/export/reopen; provenance/hash; A0003–A0006 |
| A0008 | Один end-to-end обязательный song/singing recipe | Настоящее пение с текстом/музыкой, соответствие запросу и качество по протоколу; speech/test tone не принимаются; A0005–A0006 |
| A0009 | Согласованность всех альтернативных поддерживаемых entrypoints | GUI/CLI/agent при одном запросе не расходятся в required stages, cancellation и success semantics; A0007–A0008 |
| A0010 | Устойчивость хранения и пересоздания проекта | Restart/crash/locked file/full disk/migration не повреждают прежние результаты; atomic writes и recovery проверены |
| A0011 | Model lifecycle на чистой установке | Выбор/права/download/resume/hash verification/offline cache/delete/upgrade; corrupt/partial weights fail closed |
| A0012 | Изоляция несовместимых model runtimes | Реальная успешная установка и запуск каждого заявленного backend; resolver rejection не принимается за успешную установку; A0011 |
| A0013 | Матрица прав на модели/голоса/sample assets и пользовательский контент | SPDX/license/source/attribution/commercial ограничения, согласия и происхождение; нет неясных прав у включённых assets |
| A0014 | Независимо наблюдаемый offline/privacy проход | OS-level процессы и сетевые обращения во всех обязательных сценариях; redacted evidence; socket monkeypatch не замена |
| A0015 | Security boundary review установленного приложения | IPC/file paths/process args/download verification/update trust; negative exploit cases; устранены critical/high |
| A0016 | Clean standard-user Windows installation | Отдельная чистая среда, без dev dependencies/admin inheritance; first run/ACL/runtime/models и mandatory scenario; A0007–A0012 |
| A0017 | Upgrade/rollback/uninstall с сохранностью данных | Старый supported release → RC → rollback; locked processes/отмена; user projects не удалены; A0016 |
| A0018 | Проверка фактического audio playback и export formats | Не только audio.src: декодирование, воспроизведение/устройство по протоколу, save/cancel/overwrite, экспорт/повторный импорт; A0007–A0008 |
| A0019 | Репрезентативная музыкальная оценка | Набор жанров/языков/длительностей/seed и реальное прослушивание с рубрикой; критические артефакты устранены; A0007–A0008 |
| A0020 | Длительные и последовательные сессии | Несколько проектов/jobs, длинный supported render, peak/steady memory, disk cleanup, responsiveness; нет накопления leak; A0006–A0008 |
| A0021 | Windows usability/accessibility/error recovery | Keyboard/focus/scaling/high contrast, ясные статусы, отсутствие недостижимых кнопок; Unicode/пробелы/длинные пути; реальные сценарии |
| A0022 | Supportable performance budgets | Cold/warm time, RAM/VRAM/disk/download size и честные ограничения по фактическим профилям; регрессия относительно baseline; A0005,A0020 |
| A0023 | Обязательная CI release matrix без скрытых skipped failures | Unit/integration/installed Windows/реальные backend lanes, артефакты и точный source; mocks отдельно от acceptance |
| A0024 | Reproducible release provenance и dependency inventory | Locked toolchain/deps/SBOM/model manifests, build instructions, known vulnerabilities disposition; artifact связан с source |
| A0025 | Подпись и безопасное распространение в согласованной политике выпуска | Проверка подписи/целостности/upgrade trust; если внешний сертификат недоступен, gate открыт, не фиктивно подписан; A0024 |
| A0026 | Документация соответствует именно испытанному installer | Install/first song/models/hardware/offline/rights/errors/uninstall, без обещаний неподдержанных режимов; A0016–A0022 |
| A0027 | Независимый consumer acceptance последнего RC | Другой проверяющий/изолированная среда по фиксированным inputs; не вызов внутренней функции автором; A0016,A0019,A0026 |
| A0028 | Полный regression sweep после последнего изменения RC | Все обязательные T/A evidence применимы к последнему binary/dependency set; новые изменения инвалидируют затронутые evidence; A0023–A0027 |
| A0029 | Release readiness review | Нет открытых P0/P1/critical requirements; T/A матрица полна; limitations явно согласованы; acceptance owners подтверждены; A0028 |
| A0030 | Публикация испытанного artifact и проверка доставки | Скачать опубликованный installer, сравнить hash/signature, повторить clean install smoke; release notes/support/rollback; A0029, T1000 |

## Финальный выпускной протокол

Приложение считается готовым только для явно указанной и доказанной области
поддержки. Нельзя незаметно исключить пение, GPU или иной обязательный режим,
чтобы пройти ворота. Изменение обязательного scope требует решения пользователя,
а не удобства реализации. Нет обещания отсутствия любых будущих дефектов.

Выпускной протокол содержит: версию/source/build toolchain, installer hash и
signature policy, Windows/backend matrix, проверенные пользовательские сценарии,
quality/listening/privacy/security отчёты, результаты installation/update/uninstall,
решения по known issues, список обязательных T/A с evidence, release owner,
инструкцию восстановления и фактическую проверку опубликованного файла.

Не публиковать финальное «готово», если хотя бы один обязательный gate не выполнен.
Не публиковать новую версию лишь потому, что был слит documentation handoff PR.

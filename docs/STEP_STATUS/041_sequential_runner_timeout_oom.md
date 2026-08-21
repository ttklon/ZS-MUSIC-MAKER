# PLAN_v39 — ШАГ 041: SequentialAIRunner — timeout и OOM-защита

## Реализованный runtime contract

`AIStage` получил необязательный `timeout_sec`. По умолчанию stage ограничена **600 секундами**, роли `music_generation` и `music_stereo` — **1800 секундами**; явное значение stage имеет приоритет. До запуска и после загрузки модели runner измеряет VRAM, а превышение `vram_budget_gb` (по умолчанию hardware budget registry, 12 GB) немедленно завершает stage с `ok=False` и причиной, начинающейся с `oom:`.

| Механизм | Поведение |
|---|---|
| Последовательность | Stage запускаются только в одном цикле `run`; между ними в `finally` выполняются `registry.unload()` и `gc.collect()`. |
| Watchdog | Daemon watchdog-thread всегда фиксирует истечение лимита. На POSIX main-thread дополнительно использует `SIGALRM`, который прерывает исполняемую Python stage c `StageTimeoutError`. |
| Timeout result | Истёкшая стадия получает `ok=False`, `error=stage '<name>' timed out after …s`; последующие стадии продолжаются. |
| OOM result | Stage не вызывается при VRAM выше budget; `error` содержит измеренное значение, budget и фазу проверки. |
| Наблюдаемость | Каждый `StageReport`/`RunReport.to_dict()` содержит `timeout_sec`, `vram_before_gb` и `vram_after_gb`; runner логирует matrix времени и VRAM. |

## Ограничение безопасности

Python не предоставляет безопасного способа убить произвольный поток, уже выполняющий CUDA/C extension. Поэтому runner **не делает небезопасный thread kill**. В production Linux/POSIX путь с `SIGALRM` прерывает зависший Python-вызов; если конкретная нативная библиотека игнорирует сигналы до возврата, watchdog честно отмечает timeout сразу после возврата, а `finally` освобождает registry handle. Для полностью неперехватываемого native inference требуется изолированный process boundary, а не уничтожение потока внутри процесса.

## CLI dry-run

Исправлен приоритет аргументов в `main.py`: сочетание `--ai --dry-run` теперь запускает `run_ai_pipeline(..., dry_run=True)` и, следовательно, проверяет именно новый `SequentialAIRunner`; до исправления `--dry-run` перехватывался legacy full-pipeline веткой. Сквозной запуск завершился за 0.6 s. В sandbox все тяжёлые роли честно работали через fallback/skipped, а JSON каждого stage содержал timeout и VRAM telemetry; музыкальные роли получили 1800 s.

## Доказательства

Добавлены регрессии: timeout slow Python stage на 0.05 s, продолжение следующей stage, отказ при fake VRAM 13 GB на budget 12 GB до вызова функции и выбор extended timeout музыкальной роли. На момент приёмки: `pytest tests/test_ai_layer.py -q` — **29 passed**; `pytest tests/ -q` — **99 passed**; `python main.py --ai --dry-run` — **успешно**; `compileall` — успешно; AST-аудит — **0 dead imports**.

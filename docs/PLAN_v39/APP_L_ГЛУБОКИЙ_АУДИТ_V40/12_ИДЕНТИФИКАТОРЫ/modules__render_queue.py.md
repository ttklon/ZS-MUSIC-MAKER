# Идентификаторы `modules/render_queue.py`

## Имена (ast.Name) (уникальных: 61)

| Имя | Использований |
|-----|--------------:|
| `self` | 45 |
| `item` | 18 |
| `i` | 18 |
| `str` | 11 |
| `it` | 11 |
| `dict` | 9 |
| `QueueItem` | 7 |
| `list` | 6 |
| `float` | 5 |
| `c` | 5 |
| `len` | 5 |
| `STATE_FILE` | 4 |
| `d` | 4 |
| `time` | 4 |
| `recipe` | 3 |
| `done` | 3 |
| `next_item` | 3 |
| `json` | 3 |
| `threading` | 3 |
| `k` | 3 |
| `ROOT` | 2 |
| `QUEUE_DIR` | 2 |
| `progress` | 2 |
| `stage` | 2 |
| `q` | 2 |
| `print` | 2 |
| `errs` | 2 |
| `pend` | 2 |
| `Exception` | 2 |
| `res` | 2 |
| `r` | 2 |
| `v` | 2 |
| `e` | 2 |
| `dataclass` | 1 |
| `id` | 1 |
| `status` | 1 |
| `project_dir` | 1 |
| `error` | 1 |
| `started_at` | 1 |
| `finished_at` | 1 |
| `result_paths` | 1 |
| `bool` | 1 |
| `__name__` | 1 |
| `field` | 1 |
| `orchestrator` | 1 |
| `log` | 1 |
| `RenderQueue` | 1 |
| `asdict` | 1 |
| `_load_state` | 1 |
| `_save_state` | 1 |
| `Callable` | 1 |
| `recipes` | 1 |
| `Path` | 1 |
| `__file__` | 1 |
| `items` | 1 |
| `item_id` | 1 |
| `Orchestrator` | 1 |
| `on_stage` | 1 |
| `probe_hw` | 1 |
| `make_logger` | 1 |
| `uuid` | 1 |

## Вызванные функции/методы (ast.Call) (уникальных: 43)

| Имя | Использований |
|-----|--------------:|
| `_persist` | 6 |
| `len` | 5 |
| `log` | 4 |
| `get` | 3 |
| `dumps` | 2 |
| `QueueItem` | 2 |
| `append` | 2 |
| `time` | 2 |
| `to_dict` | 2 |
| `field` | 1 |
| `exists` | 1 |
| `write_text` | 1 |
| `RenderQueue` | 1 |
| `print` | 1 |
| `resolve` | 1 |
| `asdict` | 1 |
| `Event` | 1 |
| `_restore` | 1 |
| `_load_state` | 1 |
| `_save_state` | 1 |
| `clear` | 1 |
| `Thread` | 1 |
| `start` | 1 |
| `set` | 1 |
| `loads` | 1 |
| `enqueue` | 1 |
| `is_alive` | 1 |
| `is_set` | 1 |
| `_pick_next` | 1 |
| `_process` | 1 |
| `run_pipeline` | 1 |
| `strftime` | 1 |
| `status_summary` | 1 |
| `Path` | 1 |
| `read_text` | 1 |
| `sleep` | 1 |
| `Orchestrator` | 1 |
| `float` | 1 |
| `probe_hw` | 1 |
| `make_logger` | 1 |
| `str` | 1 |
| `uuid4` | 1 |
| `items` | 1 |

## Обращения к атрибутам (.attr) (уникальных: 45)

| Имя | Использований |
|-----|--------------:|
| `items` | 16 |
| `status` | 12 |
| `_persist` | 6 |
| `log` | 5 |
| `_worker` | 5 |
| `orchestrator` | 4 |
| `_stop` | 4 |
| `id` | 4 |
| `get` | 3 |
| `dumps` | 2 |
| `Thread` | 2 |
| `append` | 2 |
| `time` | 2 |
| `result_paths` | 2 |
| `progress` | 2 |
| `to_dict` | 2 |
| `error` | 2 |
| `parents` | 1 |
| `exists` | 1 |
| `write_text` | 1 |
| `started_at` | 1 |
| `resolve` | 1 |
| `Event` | 1 |
| `_restore` | 1 |
| `clear` | 1 |
| `start` | 1 |
| `set` | 1 |
| `finished_at` | 1 |
| `loads` | 1 |
| `enqueue` | 1 |
| `is_alive` | 1 |
| `_run_loop` | 1 |
| `is_set` | 1 |
| `_pick_next` | 1 |
| `_process` | 1 |
| `stage` | 1 |
| `run_pipeline` | 1 |
| `recipe` | 1 |
| `strftime` | 1 |
| `status_summary` | 1 |
| `read_text` | 1 |
| `hex` | 1 |
| `sleep` | 1 |
| `uuid4` | 1 |
| `__dataclass_fields__` | 1 |

## Строковые литералы (уникальных: 27)

| Имя | Использований |
|-----|--------------:|
| `pending` | 7 |
| `done` | 5 |
| `error` | 4 |
| `` | 3 |
| `running` | 3 |
| `utf-8` | 2 |
| `total` | 2 |
| `status` | 2 |
| `queue` | 1 |
| `queue_state.json` | 1 |
| `\n    Автономная очередь. Использует Orchestrator для реального рендера.\n    Работает в фоне (демонический поток).\n   ` | 1 |
| `__main__` | 1 |
| `output` | 1 |
| `[queue] worker started` | 1 |
| `[queue] stop requested` | 1 |
| `errors` | 1 |
| `delivered_paths` | 1 |
| `generated_at` | 1 |
| `[queue] enqueued ` | 1 |
| ` (` | 1 |
| `)` | 1 |
| `cancelled` | 1 |
| `%Y-%m-%d %H:%M:%S` | 1 |
| `theme` | 1 |
| `?` | 1 |
| `[queue] ` | 1 |
| ` FAILED: ` | 1 |

## Числовые литералы (уникальных: 10)

| Имя | Использований |
|-----|--------------:|
| `0` | 5 |
| `0.0` | 3 |
| `1` | 2 |
| `False` | 2 |
| `2` | 2 |
| `True` | 2 |
| `1.0` | 1 |
| `3` | 1 |
| `10` | 1 |
| `400` | 1 |
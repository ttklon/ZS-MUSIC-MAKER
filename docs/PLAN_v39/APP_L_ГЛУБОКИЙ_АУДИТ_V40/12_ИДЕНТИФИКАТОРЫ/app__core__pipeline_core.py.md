# Идентификаторы `app/core/pipeline_core.py`

## Имена (ast.Name) (уникальных: 55)

| Имя | Использований |
|-----|--------------:|
| `self` | 27 |
| `str` | 14 |
| `res` | 12 |
| `logger` | 10 |
| `stage` | 10 |
| `Any` | 7 |
| `StageResult` | 6 |
| `cp_path` | 6 |
| `Dict` | 5 |
| `duration` | 5 |
| `PipelineContext` | 4 |
| `Exception` | 4 |
| `time` | 4 |
| `f` | 4 |
| `age` | 4 |
| `e` | 4 |
| `data` | 4 |
| `name` | 3 |
| `project_id` | 3 |
| `logging` | 3 |
| `start_time` | 3 |
| `context` | 3 |
| `error_msg` | 3 |
| `Path` | 3 |
| `result` | 3 |
| `dataclass` | 2 |
| `bool` | 2 |
| `config` | 2 |
| `field` | 2 |
| `func` | 2 |
| `dict` | 2 |
| `result_data` | 2 |
| `PipelineStage` | 2 |
| `use_checkpoints` | 2 |
| `Callable` | 2 |
| `checkpoint_dir` | 2 |
| `stage_name` | 2 |
| `open` | 2 |
| `json` | 2 |
| `int` | 2 |
| `r` | 2 |
| `ok` | 1 |
| `output` | 1 |
| `duration_sec` | 1 |
| `float` | 1 |
| `error` | 1 |
| `results` | 1 |
| `shared_data` | 1 |
| `CHECKPOINT_TTL_SEC` | 1 |
| `Optional` | 1 |
| `List` | 1 |
| `gc` | 1 |
| `all` | 1 |
| `os` | 1 |
| `type` | 1 |

## Вызванные функции/методы (ast.Call) (уникальных: 27)

| Имя | Использований |
|-----|--------------:|
| `info` | 5 |
| `time` | 4 |
| `StageResult` | 3 |
| `field` | 2 |
| `Path` | 2 |
| `error` | 2 |
| `open` | 2 |
| `warning` | 2 |
| `int` | 2 |
| `basicConfig` | 1 |
| `getLogger` | 1 |
| `PipelineContext` | 1 |
| `mkdir` | 1 |
| `append` | 1 |
| `func` | 1 |
| `PipelineStage` | 1 |
| `get` | 1 |
| `execute` | 1 |
| `_save_checkpoint` | 1 |
| `collect` | 1 |
| `dump` | 1 |
| `exists` | 1 |
| `all` | 1 |
| `type` | 1 |
| `stat` | 1 |
| `load` | 1 |
| `values` | 1 |

## Обращения к атрибутам (.attr) (уникальных: 32)

| Имя | Использований |
|-----|--------------:|
| `name` | 16 |
| `context` | 7 |
| `info` | 5 |
| `results` | 5 |
| `checkpoint_dir` | 4 |
| `time` | 4 |
| `ok` | 4 |
| `stages` | 3 |
| `func` | 2 |
| `project_id` | 2 |
| `error` | 2 |
| `warning` | 2 |
| `basicConfig` | 1 |
| `getLogger` | 1 |
| `INFO` | 1 |
| `mkdir` | 1 |
| `append` | 1 |
| `get` | 1 |
| `execute` | 1 |
| `_save_checkpoint` | 1 |
| `collect` | 1 |
| `dump` | 1 |
| `environ` | 1 |
| `exists` | 1 |
| `CHECKPOINT_TTL_SEC` | 1 |
| `__name__` | 1 |
| `output` | 1 |
| `duration_sec` | 1 |
| `st_mtime` | 1 |
| `stat` | 1 |
| `load` | 1 |
| `values` | 1 |

## Строковые литералы (уникальных: 32)

| Имя | Использований |
|-----|--------------:|
| `stage=` | 3 |
| `output` | 3 |
| `.json` | 2 |
| `: ` | 2 |
| `utf-8` | 2 |
| `ok` | 2 |
| `duration` | 2 |
| `PipelineCore` | 1 |
| `%(asctime)s - %(name)s - %(levelname)s - %(message)s` | 1 |
| `Сохраняет состояние стадии на диск (в безопасном JSON формате).` | 1 |
| `1` | 1 |
| `project_id` | 1 |
| `status` | 1 |
| `results` | 1 |
| ` event=start` | 1 |
| `checkpoints` | 1 |
| `Launching pipeline for project: ` | 1 |
| `ZSMM_NO_CHECKPOINTS` | 1 |
| `completed` | 1 |
| `failed` | 1 |
| ` event=ok duration_ms=` | 1 |
| ` event=failed error=` | 1 |
| `w` | 1 |
| `Failed to save checkpoint for ` | 1 |
| `Pipeline halted at stage ` | 1 |
| `Checkpoint for ` | 1 |
| ` expired (` | 1 |
| `h), re-running stage` | 1 |
| `Loading checkpoint for stage: ` | 1 |
| `r` | 1 |
| `Checkpoint corrupted for ` | 1 |
| `, re-running. Error: ` | 1 |

## Числовые литералы (уникальных: 6)

| Имя | Использований |
|-----|--------------:|
| `True` | 4 |
| `False` | 3 |
| `0.0` | 2 |
| `3600` | 2 |
| `24` | 1 |
| `1000` | 1 |
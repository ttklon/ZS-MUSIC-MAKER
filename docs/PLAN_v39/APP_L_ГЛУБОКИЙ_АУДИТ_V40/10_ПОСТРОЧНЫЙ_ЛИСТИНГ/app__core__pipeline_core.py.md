# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/pipeline_core.py`

**Всего строк:** 146

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 67 | 45.9 |
| blank | 18 | 12.3 |
| docstring | 12 | 8.2 |
| import | 8 | 5.5 |
| try_block | 8 | 5.5 |
| comment | 7 | 4.8 |
| branch | 7 | 4.8 |
| def | 6 | 4.1 |
| class | 4 | 2.7 |
| return | 4 | 2.7 |
| decorator | 2 | 1.4 |
| stmt | 2 | 1.4 |
| loop | 1 | 0.7 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — pipeline_core.py (GOD MODE)
    4 [docstring ] ========================================================================
    5 [docstring ] Новое ядро пайплайна. Заменяет монструозный orchestrator.py.
    6 [docstring ] Реализует паттерн "Цепочка задач" с типизацией и обработкой ошибок.
    7 [docstring ] """
    8 [blank     ] 
    9 [import    ] import time
   10 [import    ] import logging
   11 [import    ] import gc
   12 [import    ] import json
   13 [import    ] import os
   14 [import    ] from pathlib import Path
   15 [import    ] from typing import Dict, Any, List, Callable, Optional
   16 [import    ] from dataclasses import dataclass, field
   17 [blank     ] 
   18 [comment   ] # Настройка профессионального логирования
   19 [code      ] logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
   20 [code      ] logger = logging.getLogger("PipelineCore")
   21 [blank     ] 
   22 [decorator ] @dataclass
   23 [class     ] class StageResult:
   24 [code      ]     name: str
   25 [code      ]     ok: bool
   26 [code      ]     output: Any = None
   27 [code      ]     duration_sec: float = 0.0
   28 [code      ]     error: Optional[str] = None
   29 [blank     ] 
   30 [decorator ] @dataclass
   31 [class     ] class PipelineContext:
   32 [code      ]     project_id: str
   33 [code      ]     config: Dict[str, Any]
   34 [code      ]     results: Dict[str, StageResult] = field(default_factory=dict)
   35 [code      ]     shared_data: Dict[str, Any] = field(default_factory=dict)
   36 [blank     ] 
   37 [class     ] class PipelineStage:
   38 [def       ]     def __init__(self, name: str, func: Callable[[PipelineContext], Any]):
   39 [code      ]         self.name = name
   40 [code      ]         self.func = func
   41 [blank     ] 
   42 [def       ]     def execute(self, context: PipelineContext) -> StageResult:
   43 [code      ]         start_time = time.time()
   44 [code      ]         logger.info(f"stage={self.name} event=start")
   45 [try_block ]         try:
   46 [code      ]             result_data = self.func(context)
   47 [code      ]             duration = time.time() - start_time
   48 [code      ]             res = StageResult(name=self.name, ok=True, output=result_data, duration_sec=duration)
   49 [code      ]             context.results[self.name] = res
   50 [code      ]             logger.info(f"stage={self.name} event=ok duration_ms={int(duration*1000)}")
   51 [return    ]             return res
   52 [try_block ]         except Exception as e:
   53 [code      ]             duration = time.time() - start_time
   54 [code      ]             error_msg = f"stage={self.name} event=failed error={type(e).__name__}: {e}"
   55 [code      ]             logger.error(error_msg)
   56 [code      ]             res = StageResult(name=self.name, ok=False, error=error_msg, duration_sec=duration)
   57 [code      ]             context.results[self.name] = res
   58 [return    ]             return res
   59 [blank     ] 
   60 [class     ] class ZSPipeline:
   61 [def       ]     def __init__(
   62 [code      ]         self,
   63 [code      ]         project_id: str,
   64 [code      ]         config: Dict[str, Any],
   65 [code      ]         checkpoint_dir: Path | str | None = None,
   66 [code      ]     ):
   67 [docstring ]         """Создать пайплайн с опциональным checkpoint-каталогом конкретного запуска.
   68 [blank     ] 
   69 [docstring ]         Старый путь ``output/<project_id>/checkpoints`` сохранён по умолчанию.
   70 [docstring ]         Явный путь нужен изолированным запускам (например, smoke God Mode),
   71 [docstring ]         где артефакты располагаются в отдельном ``out_root``.
   72 [docstring ]         """
   73 [code      ]         self.context = PipelineContext(project_id=project_id, config=config)
   74 [code      ]         self.stages: List[PipelineStage] = []
   75 [code      ]         self.checkpoint_dir = (
   76 [code      ]             Path(checkpoint_dir)
   77 [branch    ]             if checkpoint_dir is not None
   78 [code      ]             else Path("output") / project_id / "checkpoints"
   79 [code      ]         )
   80 [code      ]         self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
   81 [blank     ] 
   82 [def       ]     def add_stage(self, name: str, func: Callable[[PipelineContext], Any]):
   83 [code      ]         self.stages.append(PipelineStage(name, func))
   84 [return    ]         return self
   85 [blank     ] 
   86 [def       ]     def _save_checkpoint(self, stage_name: str, result: StageResult):
   87 [docstring ]         """Сохраняет состояние стадии на диск (в безопасном JSON формате)."""
   88 [code      ]         cp_path = self.checkpoint_dir / f"{stage_name}.json"
   89 [try_block ]         try:
   90 [stmt      ]             with open(cp_path, "w", encoding="utf-8") as f:
   91 [code      ]                 json.dump({
   92 [code      ]                     "ok": result.ok,
   93 [code      ]                     "output": result.output,
   94 [code      ]                     "duration": result.duration_sec
   95 [code      ]                 }, f, ensure_ascii=False, default=str)
   96 [try_block ]         except Exception as e:
   97 [code      ]             logger.warning(f"Failed to save checkpoint for {stage_name}: {e}")
   98 [blank     ] 
   99 [comment   ]     # v30: чекпоинты живут максимум 24 часа — старый fail-чекпоинт не
  100 [comment   ]     # должен вечно блокировать пайплайн после исправления кода.
  101 [code      ]     CHECKPOINT_TTL_SEC = 24 * 3600
  102 [blank     ] 
  103 [def       ]     def run(self, use_checkpoints: bool = True) -> Dict[str, Any]:
  104 [code      ]         logger.info(f"Launching pipeline for project: {self.context.project_id}")
  105 [blank     ] 
  106 [comment   ]         # v30: ZSMM_NO_CHECKPOINTS=1 полностью отключает чтение чекпоинтов
  107 [branch    ]         if os.environ.get("ZSMM_NO_CHECKPOINTS") == "1":
  108 [code      ]             use_checkpoints = False
  109 [blank     ] 
  110 [loop      ]         for stage in self.stages:
  111 [comment   ]             # Проверка чекпоинта (JSON формат для безопасности)
  112 [code      ]             cp_path = self.checkpoint_dir / f"{stage.name}.json"
  113 [branch    ]             if use_checkpoints and cp_path.exists():
  114 [try_block ]                 try:
  115 [code      ]                     age = time.time() - cp_path.stat().st_mtime
  116 [try_block ]                 except Exception:
  117 [code      ]                     age = 0.0
  118 [branch    ]                 if age > self.CHECKPOINT_TTL_SEC:
  119 [code      ]                     logger.info(f"Checkpoint for {stage.name} expired ({int(age/3600)}h), re-running stage")
  120 [branch    ]                 else:
  121 [code      ]                     logger.info(f"Loading checkpoint for stage: {stage.name}")
  122 [try_block ]                     try:
  123 [stmt      ]                         with open(cp_path, "r", encoding="utf-8") as f:
  124 [code      ]                             data = json.load(f)
  125 [code      ]                         res = StageResult(name=stage.name, ok=data["ok"], output=data["output"], duration_sec=data["duration"])
  126 [code      ]                         self.context.results[stage.name] = res
  127 [branch    ]                         if not res.ok: break
  128 [code      ]                         continue
  129 [try_block ]                     except Exception as e:
  130 [code      ]                         logger.warning(f"Checkpoint corrupted for {stage.name}, re-running. Error: {e}")
  131 [blank     ] 
  132 [code      ]             res = stage.execute(self.context)
  133 [code      ]             self._save_checkpoint(stage.name, res)
  134 [blank     ]             
  135 [comment   ]             # Принудительная очистка памяти после каждой стадии
  136 [code      ]             gc.collect()
  137 [blank     ]             
  138 [branch    ]             if not res.ok:
  139 [code      ]                 logger.error(f"Pipeline halted at stage {stage.name}")
  140 [code      ]                 break
  141 [blank     ]         
  142 [return    ]         return {
  143 [code      ]             "project_id": self.context.project_id,
  144 [code      ]             "status": "completed" if all(r.ok for r in self.context.results.values()) else "failed",
  145 [code      ]             "results": self.context.results
  146 [code      ]         }
```
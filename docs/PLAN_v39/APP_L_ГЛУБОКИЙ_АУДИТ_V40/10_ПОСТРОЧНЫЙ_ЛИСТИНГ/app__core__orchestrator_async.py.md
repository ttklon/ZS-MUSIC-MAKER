# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/orchestrator_async.py`

**Всего строк:** 118

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 58 | 49.2 |
| blank | 20 | 16.9 |
| import | 9 | 7.6 |
| comment | 6 | 5.1 |
| docstring | 6 | 5.1 |
| branch | 5 | 4.2 |
| async_def | 4 | 3.4 |
| return | 3 | 2.5 |
| class | 2 | 1.7 |
| try_block | 2 | 1.7 |
| decorator | 1 | 0.8 |
| def | 1 | 0.8 |
| stmt | 1 | 0.8 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — orchestrator_async.py (GOD MODE)
    4 [docstring ] ========================================================================
    5 [docstring ] Асинхронный оркестратор для параллельной обработки стадий.
    6 [docstring ] Позволяет одновременно генерировать бит, чистить вокал и анализировать гармонию.
    7 [docstring ] """
    8 [blank     ] 
    9 [import    ] import asyncio
   10 [import    ] import time
   11 [import    ] import os
   12 [import    ] import json
   13 [import    ] from pathlib import Path
   14 [import    ] from typing import Any, List, Optional, Callable
   15 [import    ] from dataclasses import dataclass, asdict
   16 [blank     ] 
   17 [decorator ] @dataclass
   18 [class     ] class AsyncStage:
   19 [code      ]     name: str
   20 [code      ]     ok: bool = False
   21 [code      ]     duration_sec: float = 0.0
   22 [code      ]     output: Any = None
   23 [code      ]     reason: Optional[str] = None
   24 [blank     ]     
   25 [async_def ] async def run_stage_async(name: str, coro: Callable) -> AsyncStage:
   26 [code      ]     t0 = time.time()
   27 [code      ]     stage = AsyncStage(name=name)
   28 [try_block ]     try:
   29 [comment   ]         # Если это корутина - ждем, если обычная функция - запускаем в треде
   30 [branch    ]         if asyncio.iscoroutinefunction(coro):
   31 [code      ]             res = await coro()
   32 [branch    ]         else:
   33 [code      ]             res = await asyncio.to_thread(coro)
   34 [blank     ]             
   35 [code      ]         stage.ok = True
   36 [code      ]         stage.output = res
   37 [try_block ]     except Exception as e:
   38 [code      ]         stage.ok = False
   39 [code      ]         stage.reason = f"{type(e).__name__}: {e}"
   40 [code      ]     stage.duration_sec = round(time.time() - t0, 3)
   41 [return    ]     return stage
   42 [blank     ] 
   43 [class     ] class AsyncOrchestrator:
   44 [def       ]     def __init__(self, project_id: str, out_root: Path):
   45 [code      ]         self.project_id = project_id
   46 [code      ]         self.out_root = out_root
   47 [code      ]         self.out_root.mkdir(parents=True, exist_ok=True)
   48 [code      ]         self.stages: List[AsyncStage] = []
   49 [comment   ]         # v26: Ограничиваем параллелизм количеством ядер для стабильности
   50 [import    ]         import multiprocessing
   51 [code      ]         self.semaphore = asyncio.Semaphore(max(1, multiprocessing.cpu_count() - 1))
   52 [blank     ] 
   53 [async_def ]     async def _run_limited(self, name: str, coro: Callable):
   54 [code      ]         async with self.semaphore:
   55 [return    ]             return await run_stage_async(name, coro)
   56 [blank     ] 
   57 [async_def ]     async def run_pipeline(self, wizard_state: dict):
   58 [code      ]         t_start = time.time()
   59 [blank     ]         
   60 [import    ]         from modules import beat_constructor, phonk_engine, voice_cleaner, mastering_pro
   61 [blank     ]         
   62 [code      ]         bpm = int(wizard_state.get("bpm_override") or 130)
   63 [code      ]         genre = wizard_state.get("genre", "drift_phonk")
   64 [blank     ]         
   65 [comment   ]         # 1. Параллельный запуск генерации бита и колокольчиков (через семафор)
   66 [code      ]         tasks = [
   67 [code      ]             self._run_limited("beat_gen", lambda: beat_constructor.construct_beat(
   68 [code      ]                 groove={}, samples=[], 
   69 [code      ]                 style_vector={"target_bpm": bpm, "target_mode": "minor", "genre": genre},
   70 [code      ]                 out_name="beat.wav"
   71 [code      ]             )),
   72 [code      ]             self._run_limited("cowbell_gen", lambda: phonk_engine.create_cowbell_melody(
   73 [code      ]                 [440, 523, 392, 440], bpm, str(self.out_root / "cowbells.wav")
   74 [code      ]             ))
   75 [code      ]         ]
   76 [blank     ]         
   77 [comment   ]         # Если есть вокал - добавляем очистку в параллель
   78 [code      ]         vocal_in = wizard_state.get("vocal_input_path")
   79 [branch    ]         if vocal_in and os.path.exists(vocal_in):
   80 [code      ]             tasks.append(self._run_limited("vocal_clean", lambda: voice_cleaner.clean_vocal(
   81 [code      ]                 vocal_in, str(self.out_root / "vocal_cleaned.wav")
   82 [code      ]             )))
   83 [blank     ]             
   84 [code      ]         results = await asyncio.gather(*tasks)
   85 [code      ]         self.stages.extend(results)
   86 [blank     ]         
   87 [comment   ]         # 2. Финальный мастеринг (зависит от результатов)
   88 [code      ]         beat_stage = next((s for s in results if s.name == "beat_gen"), None)
   89 [branch    ]         if beat_stage and beat_stage.ok:
   90 [code      ]             beat_path = beat_stage.output.get("beat_path")
   91 [code      ]             master_wav = str(self.out_root / "masters" / "master_async.wav")
   92 [blank     ]             
   93 [code      ]             master_stage = await run_stage_async("mastering", lambda: mastering_pro.process_mastering(
   94 [code      ]                 beat_path, master_wav, target_lufs=-12.0
   95 [code      ]             ))
   96 [code      ]             self.stages.append(master_stage)
   97 [blank     ]             
   98 [code      ]         total_duration = round(time.time() - t_start, 2)
   99 [blank     ]         
  100 [code      ]         final_res = {
  101 [code      ]             "project_id": self.project_id,
  102 [code      ]             "status": "completed" if all(s.ok for s in self.stages) else "partial",
  103 [code      ]             "duration_sec": total_duration,
  104 [code      ]             "stages": [asdict(s) for s in self.stages]
  105 [code      ]         }
  106 [blank     ]         
  107 [stmt      ]         with open(self.out_root / "async_meta.json", "w") as f:
  108 [code      ]             json.dump(final_res, f, indent=2, default=str)
  109 [blank     ]             
  110 [return    ]         return final_res
  111 [blank     ] 
  112 [async_def ] async def main_async():
  113 [code      ]     orch = AsyncOrchestrator("async_test", Path("./output/async_test"))
  114 [code      ]     res = await orch.run_pipeline({"genre": "phonk", "bpm_override": 140})
  115 [code      ]     print(f"Async Pipeline Done in {res['duration_sec']}s")
  116 [blank     ] 
  117 [branch    ] if __name__ == "__main__":
  118 [code      ]     asyncio.run(main_async())
```
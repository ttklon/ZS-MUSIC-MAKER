# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/runtime_orchestrator.py`

**Всего строк:** 149

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 89 | 59.7 |
| blank | 15 | 10.1 |
| branch | 13 | 8.7 |
| import | 8 | 5.4 |
| def | 7 | 4.7 |
| try_block | 5 | 3.4 |
| loop | 4 | 2.7 |
| return | 3 | 2.0 |
| class | 2 | 1.3 |
| stmt | 2 | 1.3 |
| decorator | 1 | 0.7 |

## Полный листинг с классификацией
```
    1 [import    ] from __future__ import annotations
    2 [blank     ] 
    3 [import    ] import threading
    4 [import    ] import time
    5 [import    ] import uuid
    6 [import    ] from dataclasses import dataclass, field
    7 [import    ] from pathlib import Path
    8 [import    ] from typing import Any
    9 [blank     ] 
   10 [import    ] from app.core.orchestrator import run_full_pipeline
   11 [blank     ] 
   12 [code      ] ROOT = Path(__file__).resolve().parents[1]
   13 [blank     ] 
   14 [blank     ] 
   15 [decorator ] @dataclass
   16 [class     ] class Job:
   17 [code      ]     track_id: str
   18 [code      ]     recipe: dict[str, Any]
   19 [code      ]     status: str = "pending"
   20 [code      ]     progress: float = 0.0
   21 [code      ]     stage: str = "queued"
   22 [code      ]     project_dir: str = ""
   23 [code      ]     error: str = ""
   24 [code      ]     started_at: float = 0.0
   25 [code      ]     finished_at: float = 0.0
   26 [code      ]     result: dict[str, Any] = field(default_factory=dict)
   27 [blank     ] 
   28 [blank     ] 
   29 [class     ] class RuntimeOrchestrator:
   30 [def       ]     def __init__(self, log=None):
   31 [code      ]         self.log = log
   32 [code      ]         self.jobs: dict[str, Job] = {}
   33 [code      ]         self._queue: list[str] = []
   34 [code      ]         self._lock = threading.Lock()
   35 [code      ]         self._stop = threading.Event()
   36 [code      ]         self._worker: threading.Thread | None = None
   37 [code      ]         self._ensure_worker()
   38 [blank     ] 
   39 [def       ]     def _log(self, msg: str):
   40 [try_block ]         try:
   41 [branch    ]             if self.log is not None and hasattr(self.log, "info"):
   42 [code      ]                 self.log.info(msg)
   43 [branch    ]             else:
   44 [code      ]                 print(msg)
   45 [try_block ]         except Exception:
   46 [code      ]             pass
   47 [blank     ] 
   48 [def       ]     def _ensure_worker(self):
   49 [branch    ]         if self._worker and self._worker.is_alive():
   50 [return    ]             return
   51 [code      ]         self._stop.clear()
   52 [code      ]         self._worker = threading.Thread(target=self._run_loop, daemon=True)
   53 [code      ]         self._worker.start()
   54 [blank     ] 
   55 [def       ]     def enqueue(self, recipe: dict[str, Any]) -> str:
   56 [code      ]         tid = uuid.uuid4().hex[:10]
   57 [code      ]         out_dir = ROOT / "output" / "desktop_runs" / tid
   58 [code      ]         job = Job(track_id=tid, recipe=dict(recipe or {}), project_dir=str(out_dir))
   59 [stmt      ]         with self._lock:
   60 [code      ]             self.jobs[tid] = job
   61 [code      ]             self._queue.append(tid)
   62 [code      ]         self._ensure_worker()
   63 [code      ]         self._log(f"[runtime_orch] enqueued {tid}")
   64 [return    ]         return tid
   65 [blank     ] 
   66 [def       ]     def enqueue_batch(self, recipes: list[dict[str, Any]]) -> list[str]:
   67 [return    ]         return [self.enqueue(r) for r in (recipes or [])]
   68 [blank     ] 
   69 [def       ]     def _run_loop(self):
   70 [loop      ]         while not self._stop.is_set():
   71 [code      ]             tid = None
   72 [stmt      ]             with self._lock:
   73 [branch    ]                 if self._queue:
   74 [code      ]                     tid = self._queue.pop(0)
   75 [branch    ]             if not tid:
   76 [code      ]                 time.sleep(0.2)
   77 [code      ]                 continue
   78 [code      ]             job = self.jobs.get(tid)
   79 [branch    ]             if job:
   80 [code      ]                 self._process(job)
   81 [blank     ] 
   82 [def       ]     def _process(self, job: Job):
   83 [code      ]         out_dir = Path(job.project_dir)
   84 [code      ]         out_dir.mkdir(parents=True, exist_ok=True)
   85 [code      ]         job.status = "running"
   86 [code      ]         job.stage = "pipeline"
   87 [code      ]         job.progress = 0.1
   88 [code      ]         job.started_at = time.time()
   89 [try_block ]         try:
   90 [code      ]             res = run_full_pipeline(
   91 [code      ]                 job.track_id, job.recipe, dry_run=False, out_root=out_dir
   92 [code      ]             )
   93 [code      ]             job.progress = 0.92
   94 [code      ]             stages = res.get("stages") or []
   95 [code      ]             release_dir = None
   96 [code      ]             master_path = None
   97 [code      ]             hit = {}
   98 [loop      ]             for st in stages:
   99 [code      ]                 name = st.get("name")
  100 [code      ]                 out = st.get("output") or {}
  101 [branch    ]                 if name == "_stage_release_pack":
  102 [code      ]                     release_dir = out.get("path") or release_dir
  103 [branch    ]                 elif name == "_stage_polish":
  104 [code      ]                     master_path = out.get("path") or out.get("out_wav") or master_path
  105 [branch    ]                 elif name == "_stage_mastering" and not master_path:
  106 [code      ]                     master_path = (
  107 [code      ]                         (out.get("stands", {}) or {})
  108 [code      ]                         .get("streaming", {})
  109 [code      ]                         .get("out_wav")
  110 [code      ]                     )
  111 [branch    ]                 elif name == "_stage_hit_score":
  112 [code      ]                     hit = out
  113 [blank     ] 
  114 [code      ]             advice = [
  115 [code      ]                 a.strip()
  116 [loop      ]                 for a in (hit.get("actions") or [])[:4]
  117 [branch    ]                 if isinstance(a, str) and a.strip()
  118 [code      ]             ]
  119 [code      ]             flags = [
  120 [code      ]                 w.strip()
  121 [loop      ]                 for w in (res.get("warnings") or [])[:4]
  122 [branch    ]                 if isinstance(w, str) and w.strip()
  123 [code      ]             ]
  124 [blank     ] 
  125 [code      ]             job.result = {
  126 [code      ]                 "pipeline": res,
  127 [code      ]                 "master": master_path,
  128 [code      ]                 "master_path": master_path,
  129 [code      ]                 "release": {"release_dir": release_dir},
  130 [code      ]                 "ai_detector": {
  131 [code      ]                     "ok": bool(hit),
  132 [code      ]                     "verdict": hit.get("verdict"),
  133 [code      ]                     "score": hit.get("hit_score"),
  134 [code      ]                     "flags": flags,
  135 [code      ]                     "advice": advice,
  136 [code      ]                 },
  137 [code      ]             }
  138 [code      ]             job.status = "done" if res.get("verdict") not in ("FAILED",) else "error"
  139 [code      ]             job.stage = str(res.get("verdict") or "done").lower()
  140 [code      ]             job.progress = 1.0 if job.status == "done" else 0.0
  141 [branch    ]             if job.status == "error":
  142 [code      ]                 job.error = str(res.get("warnings") or ["pipeline failed"])
  143 [try_block ]         except Exception as e:
  144 [code      ]             job.status = "error"
  145 [code      ]             job.stage = "failed"
  146 [code      ]             job.error = f"{type(e).__name__}: {e}"[:500]
  147 [code      ]             job.progress = 0.0
  148 [try_block ]         finally:
  149 [code      ]             job.finished_at = time.time()
```
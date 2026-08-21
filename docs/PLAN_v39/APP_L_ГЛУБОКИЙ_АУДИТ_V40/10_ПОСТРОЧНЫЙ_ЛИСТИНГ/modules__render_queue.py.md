# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/render_queue.py`

**Всего строк:** 197

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 79 | 40.1 |
| blank | 34 | 17.3 |
| def | 19 | 9.6 |
| return | 14 | 7.1 |
| docstring | 11 | 5.6 |
| import | 11 | 5.6 |
| comment | 8 | 4.1 |
| branch | 8 | 4.1 |
| try_block | 5 | 2.5 |
| loop | 5 | 2.5 |
| class | 2 | 1.0 |
| decorator | 1 | 0.5 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v8] render_queue.py — Рендер-очередь для ночных пачек (5+ треков).
    3 [blank     ] 
    4 [docstring ] ТЗ 20.2 п.7: «Объём: ~5 треков в неделю. Добавить рендер-очередь: 5+ проектов
    5 [docstring ] на ночь. Утром — готовый набор.»
    6 [blank     ] 
    7 [docstring ] Работает поверх Orchestrator: принимает список recipe.json, запускает их
    8 [docstring ] последовательно, ведёт state, умеет восстанавливаться после перезапуска.
    9 [docstring ] """
   10 [blank     ] 
   11 [import    ] from __future__ import annotations
   12 [blank     ] 
   13 [import    ] import json
   14 [import    ] import threading
   15 [import    ] import time
   16 [import    ] import uuid
   17 [import    ] from collections.abc import Callable
   18 [import    ] from dataclasses import asdict, dataclass, field
   19 [import    ] from pathlib import Path
   20 [blank     ] 
   21 [code      ] ROOT = Path(__file__).resolve().parents[1]
   22 [code      ] QUEUE_DIR = ROOT / "output" / "queue"
   23 [code      ] STATE_FILE = QUEUE_DIR / "queue_state.json"
   24 [comment   ] # v22: ленивое создание (не при импорте)
   25 [blank     ] 
   26 [blank     ] 
   27 [decorator ] @dataclass
   28 [class     ] class QueueItem:
   29 [code      ]     id: str
   30 [code      ]     recipe: dict
   31 [code      ]     status: str = "pending"  # pending | running | done | error
   32 [code      ]     progress: float = 0.0
   33 [code      ]     stage: str = ""
   34 [code      ]     project_dir: str = ""
   35 [code      ]     error: str = ""
   36 [code      ]     started_at: float = 0.0
   37 [code      ]     finished_at: float = 0.0
   38 [code      ]     result_paths: dict = field(default_factory=dict)
   39 [blank     ] 
   40 [def       ]     def to_dict(self):
   41 [return    ]         return asdict(self)
   42 [blank     ] 
   43 [blank     ] 
   44 [def       ] def _load_state() -> list[dict]:
   45 [branch    ]     if STATE_FILE.exists():
   46 [try_block ]         try:
   47 [return    ]             return json.loads(STATE_FILE.read_text(encoding="utf-8"))
   48 [try_block ]         except Exception:
   49 [return    ]             return []
   50 [return    ]     return []
   51 [blank     ] 
   52 [blank     ] 
   53 [def       ] def _save_state(items: list[QueueItem]) -> None:
   54 [code      ]     STATE_FILE.write_text(
   55 [code      ]         json.dumps([i.to_dict() for i in items], ensure_ascii=False, indent=2),
   56 [code      ]         encoding="utf-8",
   57 [code      ]     )
   58 [blank     ] 
   59 [blank     ] 
   60 [class     ] class RenderQueue:
   61 [docstring ]     """
   62 [docstring ]     Автономная очередь. Использует Orchestrator для реального рендера.
   63 [docstring ]     Работает в фоне (демонический поток).
   64 [docstring ]     """
   65 [blank     ] 
   66 [def       ]     def __init__(self, orchestrator=None, log: Callable[[str], None] = print):
   67 [code      ]         self.items: list[QueueItem] = []
   68 [code      ]         self.orchestrator = orchestrator
   69 [code      ]         self.log = log
   70 [code      ]         self._stop = threading.Event()
   71 [code      ]         self._worker: threading.Thread | None = None
   72 [code      ]         self._restore()
   73 [blank     ] 
   74 [comment   ]     # ------------------------------------------------------- persistence
   75 [def       ]     def _restore(self):
   76 [loop      ]         for d in _load_state():
   77 [comment   ]             # Возвращаем running → pending при рестарте.
   78 [branch    ]             if d.get("status") == "running":
   79 [code      ]                 d["status"] = "pending"
   80 [code      ]             item = QueueItem(
   81 [code      ]                 **{k: v for k, v in d.items() if k in QueueItem.__dataclass_fields__}
   82 [code      ]             )
   83 [code      ]             self.items.append(item)
   84 [blank     ] 
   85 [def       ]     def _persist(self):
   86 [code      ]         _save_state(self.items)
   87 [blank     ] 
   88 [comment   ]     # ------------------------------------------------------- API
   89 [def       ]     def enqueue(self, recipe: dict) -> str:
   90 [code      ]         item = QueueItem(id=uuid.uuid4().hex[:10], recipe=recipe)
   91 [code      ]         self.items.append(item)
   92 [code      ]         self._persist()
   93 [code      ]         self.log(f"[queue] enqueued {item.id} ({recipe.get('theme', '?')})")
   94 [return    ]         return item.id
   95 [blank     ] 
   96 [def       ]     def enqueue_batch(self, recipes: list[dict]) -> list[str]:
   97 [return    ]         return [self.enqueue(r) for r in recipes]
   98 [blank     ] 
   99 [def       ]     def status_summary(self) -> dict:
  100 [code      ]         c = {"pending": 0, "running": 0, "done": 0, "error": 0}
  101 [loop      ]         for it in self.items:
  102 [code      ]             c[it.status] = c.get(it.status, 0) + 1
  103 [code      ]         c["total"] = len(self.items)
  104 [return    ]         return c
  105 [blank     ] 
  106 [def       ]     def list_items(self) -> list[dict]:
  107 [return    ]         return [i.to_dict() for i in self.items]
  108 [blank     ] 
  109 [def       ]     def cancel(self, item_id: str) -> bool:
  110 [loop      ]         for it in self.items:
  111 [branch    ]             if it.id == item_id and it.status == "pending":
  112 [code      ]                 it.status = "error"
  113 [code      ]                 it.error = "cancelled"
  114 [code      ]                 self._persist()
  115 [return    ]                 return True
  116 [return    ]         return False
  117 [blank     ] 
  118 [def       ]     def clear_done(self):
  119 [code      ]         self.items = [i for i in self.items if i.status not in ("done",)]
  120 [code      ]         self._persist()
  121 [blank     ] 
  122 [comment   ]     # ------------------------------------------------------- worker
  123 [def       ]     def start(self):
  124 [branch    ]         if self._worker and self._worker.is_alive():
  125 [return    ]             return
  126 [code      ]         self._stop.clear()
  127 [code      ]         self._worker = threading.Thread(target=self._run_loop, daemon=True)
  128 [code      ]         self._worker.start()
  129 [code      ]         self.log("[queue] worker started")
  130 [blank     ] 
  131 [def       ]     def stop(self):
  132 [code      ]         self._stop.set()
  133 [code      ]         self.log("[queue] stop requested")
  134 [blank     ] 
  135 [def       ]     def _run_loop(self):
  136 [loop      ]         while not self._stop.is_set():
  137 [code      ]             next_item = self._pick_next()
  138 [branch    ]             if not next_item:
  139 [code      ]                 time.sleep(3)
  140 [code      ]                 continue
  141 [code      ]             self._process(next_item)
  142 [blank     ] 
  143 [def       ]     def _pick_next(self) -> QueueItem | None:
  144 [loop      ]         for it in self.items:
  145 [branch    ]             if it.status == "pending":
  146 [return    ]                 return it
  147 [return    ]         return None
  148 [blank     ] 
  149 [comment   ]     # ------------------------------------------------------- run one
  150 [def       ]     def _process(self, item: QueueItem):
  151 [code      ]         item.status = "running"
  152 [code      ]         item.started_at = time.time()
  153 [code      ]         self._persist()
  154 [try_block ]         try:
  155 [branch    ]             if self.orchestrator is None:
  156 [comment   ]                 # Ленивый импорт, чтобы модуль работал автономно.
  157 [import    ]                 from app.core.orchestrator import Orchestrator
  158 [import    ]                 from app.hw_probe import probe_hw
  159 [import    ]                 from app.logger import make_logger
  160 [blank     ] 
  161 [code      ]                 self.orchestrator = Orchestrator(probe_hw(), make_logger())
  162 [blank     ] 
  163 [def       ]             def on_stage(stage: str, progress: float):
  164 [code      ]                 item.stage = stage
  165 [code      ]                 item.progress = float(progress)
  166 [code      ]                 self._persist()
  167 [blank     ] 
  168 [code      ]             res = self.orchestrator.run_pipeline(item.recipe, stage_hook=on_stage)
  169 [code      ]             item.result_paths = res or {}
  170 [code      ]             item.status = "done"
  171 [code      ]             item.progress = 1.0
  172 [try_block ]         except Exception as e:
  173 [code      ]             item.status = "error"
  174 [code      ]             item.error = str(e)[:400]
  175 [code      ]             self.log(f"[queue] {item.id} FAILED: {e}")
  176 [try_block ]         finally:
  177 [code      ]             item.finished_at = time.time()
  178 [code      ]             self._persist()
  179 [blank     ] 
  180 [comment   ]     # ------------------------------------------------------- morning report
  181 [def       ]     def morning_report(self) -> dict:
  182 [code      ]         done = [i for i in self.items if i.status == "done"]
  183 [code      ]         errs = [i for i in self.items if i.status == "error"]
  184 [code      ]         pend = [i for i in self.items if i.status == "pending"]
  185 [return    ]         return {
  186 [code      ]             "total": len(self.items),
  187 [code      ]             "done": len(done),
  188 [code      ]             "errors": len(errs),
  189 [code      ]             "pending": len(pend),
  190 [code      ]             "delivered_paths": [i.result_paths for i in done],
  191 [code      ]             "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
  192 [code      ]         }
  193 [blank     ] 
  194 [blank     ] 
  195 [branch    ] if __name__ == "__main__":
  196 [code      ]     q = RenderQueue()
  197 [code      ]     print(json.dumps(q.status_summary(), indent=2))
```
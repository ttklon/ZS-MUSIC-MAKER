# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/ai/sequential_runner.py`

**Всего строк:** 134

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 73 | 54.5 |
| blank | 15 | 11.2 |
| branch | 11 | 8.2 |
| return | 9 | 6.7 |
| def | 6 | 4.5 |
| import | 5 | 3.7 |
| class | 4 | 3.0 |
| decorator | 3 | 2.2 |
| try_block | 3 | 2.2 |
| docstring | 2 | 1.5 |
| comment | 1 | 0.7 |
| loop | 1 | 0.7 |
| raise | 1 | 0.7 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker - app/ai/sequential_runner.py (v38)
    3 [docstring ] Последовательный раннер: одна тяжёлая модель в VRAM за раз."""
    4 [import    ] from __future__ import annotations
    5 [import    ] import gc, time, logging
    6 [import    ] from dataclasses import dataclass, field
    7 [import    ] from typing import Any, Callable, Dict, List, Optional
    8 [import    ] from app.ai.registry import registry, MODEL_REGISTRY
    9 [blank     ] 
   10 [code      ] logger = logging.getLogger("SequentialAIRunner")
   11 [branch    ] if not logger.handlers:
   12 [code      ]     logging.basicConfig(level=logging.INFO,
   13 [code      ]                         format="%(asctime)s [AI] %(levelname)s %(message)s")
   14 [blank     ] 
   15 [blank     ] 
   16 [decorator ] @dataclass
   17 [class     ] class AIStage:
   18 [code      ]     name: str
   19 [code      ]     model: Optional[str]
   20 [code      ]     fn: Callable[[Any, Any], Any]
   21 [code      ]     optional: bool = False
   22 [code      ]     unload_after: bool = True
   23 [code      ]     fallback_fn: bool = True   # модели нет -> всё равно вызвать fn(None, ctx)
   24 [blank     ] 
   25 [blank     ] 
   26 [decorator ] @dataclass
   27 [class     ] class StageReport:
   28 [code      ]     name: str
   29 [code      ]     ok: bool
   30 [code      ]     used_model: Optional[str]
   31 [code      ]     device: Optional[str]
   32 [code      ]     duration_sec: float
   33 [code      ]     output_summary: str = ""
   34 [code      ]     error: Optional[str] = None
   35 [code      ]     skipped_reason: Optional[str] = None
   36 [blank     ] 
   37 [blank     ] 
   38 [decorator ] @dataclass
   39 [class     ] class RunReport:
   40 [code      ]     stages: List[StageReport] = field(default_factory=list)
   41 [code      ]     total_sec: float = 0.0
   42 [blank     ] 
   43 [def       ]     def to_dict(self) -> Dict[str, Any]:
   44 [return    ]         return {"total_sec": round(self.total_sec, 2),
   45 [code      ]                 "stages": [{"name": s.name, "ok": s.ok, "used_model": s.used_model,
   46 [code      ]                             "device": s.device, "duration_sec": round(s.duration_sec, 2),
   47 [code      ]                             "output_summary": s.output_summary, "error": s.error,
   48 [code      ]                             "skipped_reason": s.skipped_reason} for s in self.stages]}
   49 [blank     ] 
   50 [blank     ] 
   51 [class     ] class SequentialAIRunner:
   52 [def       ]     def __init__(self):
   53 [code      ]         self.stages: List[AIStage] = []
   54 [code      ]         self._sink: Dict[str, Any] = {}
   55 [blank     ] 
   56 [def       ]     def add(self, stage: AIStage) -> "SequentialAIRunner":
   57 [code      ]         self.stages.append(stage)
   58 [return    ]         return self
   59 [blank     ] 
   60 [def       ]     def sink(self) -> Dict[str, Any]:
   61 [return    ]         return self._sink
   62 [blank     ] 
   63 [def       ]     def run(self, context: Optional[Dict[str, Any]] = None) -> RunReport:
   64 [code      ]         context = context or {}
   65 [code      ]         context["sink"] = self._sink
   66 [code      ]         report = RunReport()
   67 [code      ]         t0 = time.time()
   68 [loop      ]         for st in self.stages:
   69 [code      ]             s0 = time.time()
   70 [code      ]             used, device = st.model, None
   71 [try_block ]             try:
   72 [branch    ]                 if st.model is None:
   73 [code      ]                     logger.info(f"-> stage '{st.name}' (pure DSP)")
   74 [code      ]                     out = st.fn(None, context)
   75 [code      ]                     report.stages.append(StageReport(
   76 [code      ]                         name=st.name, ok=True, used_model=None, device=None,
   77 [code      ]                         duration_sec=time.time() - s0, output_summary=_summarize(out)))
   78 [code      ]                     self._sink[st.name] = out
   79 [code      ]                     continue
   80 [branch    ]                 if st.model not in MODEL_REGISTRY:
   81 [raise     ]                     raise KeyError(f"Model role '{st.model}' not in registry")
   82 [branch    ]                 if not registry.is_available(st.model):
   83 [code      ]                     reason = f"{st.model} unavailable (deps/weights missing)"
   84 [branch    ]                     if st.optional and st.fallback_fn:
   85 [code      ]                         logger.warning(f"-> stage '{st.name}' FALLBACK ({reason})")
   86 [code      ]                         out = st.fn(None, context)
   87 [code      ]                         report.stages.append(StageReport(
   88 [code      ]                             name=st.name, ok=True, used_model=st.model, device=None,
   89 [code      ]                             duration_sec=time.time() - s0, output_summary=_summarize(out),
   90 [code      ]                             skipped_reason=reason + " -> fallback_fn ran"))
   91 [code      ]                         self._sink[st.name] = out
   92 [code      ]                         continue
   93 [branch    ]                     if st.optional:
   94 [code      ]                         report.stages.append(StageReport(
   95 [code      ]                             name=st.name, ok=True, used_model=st.model, device=None,
   96 [code      ]                             duration_sec=time.time() - s0, skipped_reason=reason))
   97 [code      ]                         continue
   98 [code      ]                     report.stages.append(StageReport(
   99 [code      ]                         name=st.name, ok=False, used_model=st.model, device=None,
  100 [code      ]                         duration_sec=time.time() - s0, error=reason))
  101 [code      ]                     continue
  102 [code      ]                 logger.info(f"-> stage '{st.name}' loading '{st.model}'")
  103 [code      ]                 loaded = registry.load(st.model)
  104 [code      ]                 device = loaded.device
  105 [code      ]                 out = st.fn(loaded.handle, context)
  106 [code      ]                 report.stages.append(StageReport(
  107 [code      ]                     name=st.name, ok=True, used_model=st.model, device=device,
  108 [code      ]                     duration_sec=time.time() - s0, output_summary=_summarize(out)))
  109 [code      ]                 self._sink[st.name] = out
  110 [try_block ]             except Exception as e:
  111 [code      ]                 logger.exception(f"x stage '{st.name}' crashed: {e}")
  112 [code      ]                 report.stages.append(StageReport(
  113 [code      ]                     name=st.name, ok=False, used_model=used, device=device,
  114 [code      ]                     duration_sec=time.time() - s0, error=str(e)))
  115 [try_block ]             finally:
  116 [branch    ]                 if st.unload_after:
  117 [code      ]                     registry.unload()
  118 [code      ]                     gc.collect()
  119 [code      ]         report.total_sec = time.time() - t0
  120 [code      ]         logger.info(f"pipeline done in {report.total_sec:.1f}s")
  121 [return    ]         return report
  122 [blank     ] 
  123 [blank     ] 
  124 [def       ] def _summarize(out: Any) -> str:
  125 [branch    ]     if out is None:
  126 [return    ]         return ""
  127 [branch    ]     if isinstance(out, (str, int, float, bool)):
  128 [code      ]         s = str(out)
  129 [return    ]         return s if len(s) < 200 else s[:200] + "..."
  130 [branch    ]     if isinstance(out, dict):
  131 [return    ]         return f"dict(keys={list(out.keys())[:6]})"
  132 [branch    ]     if isinstance(out, (list, tuple)):
  133 [return    ]         return f"{type(out).__name__}(len={len(out)})"
  134 [return    ]     return type(out).__name__
```
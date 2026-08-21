# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/orchestrator_v12_patch.py`

**Всего строк:** 144

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 68 | 47.2 |
| blank | 24 | 16.7 |
| docstring | 17 | 11.8 |
| import | 11 | 7.6 |
| try_block | 10 | 6.9 |
| branch | 5 | 3.5 |
| comment | 4 | 2.8 |
| def | 3 | 2.1 |
| return | 2 | 1.4 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v12 «Hit Locked Pro» — orchestrator_v12_patch.py
    3 [docstring ] ================================================================
    4 [blank     ] 
    5 [docstring ] Тонкая обёртка поверх v11: подсовывает мастер-пайплайн v12 в качестве
    6 [docstring ] основной точки входа и, при провале, откатывается на v11-каскад.
    7 [blank     ] 
    8 [docstring ] Соединяет:
    9 [docstring ]   1. modules.health_v12         — pre-flight
   10 [docstring ]   2. modules.master_pipeline_v12 — единый связный сценарий (ТЗ раздел 4)
   11 [docstring ]   3. modules.kpi_dashboard_v12  — итоговый отчёт для пользователя
   12 [docstring ]   4. app.core.orchestrator_v11_patch.run_full_pipeline_v11 — fallback
   13 [blank     ] 
   14 [docstring ] Никакого «магического» ML — только оркестрация.
   15 [docstring ] """
   16 [blank     ] 
   17 [import    ] from __future__ import annotations
   18 [blank     ] 
   19 [import    ] import sys
   20 [import    ] import time
   21 [import    ] import traceback
   22 [import    ] from collections.abc import Callable
   23 [import    ] from pathlib import Path
   24 [import    ] from typing import Any
   25 [blank     ] 
   26 [code      ] ROOT = Path(__file__).resolve().parents[2]
   27 [branch    ] if str(ROOT) not in sys.path:
   28 [code      ]     sys.path.insert(0, str(ROOT))
   29 [blank     ] 
   30 [blank     ] 
   31 [def       ] def _safe_print(msg: str) -> None:
   32 [try_block ]     try:
   33 [code      ]         print(msg)
   34 [try_block ]     except UnicodeEncodeError:
   35 [code      ]         sys.stdout.buffer.write((msg + "\n").encode("cp866", "replace"))
   36 [blank     ] 
   37 [blank     ] 
   38 [def       ] def run_full_pipeline_v12(
   39 [code      ]     project_id: str,
   40 [code      ]     wizard_state: dict[str, Any] | None = None,
   41 [code      ]     expert_config: dict[str, Any] | None = None,
   42 [code      ]     progress_cb: Callable[[str, float, str], None] | None = None,
   43 [code      ]     dry_run: bool = True,
   44 [code      ]     project_root: Path | None = None,
   45 [code      ] ) -> dict[str, Any]:
   46 [docstring ]     """
   47 [docstring ]     Главная точка входа v12.
   48 [blank     ] 
   49 [docstring ]     Возвращает dict со сводкой, чтобы UI мог его показать как есть.
   50 [docstring ]     """
   51 [code      ]     t0 = time.time()
   52 [code      ]     wizard_state = wizard_state or {}
   53 [code      ]     result: dict[str, Any] = {
   54 [code      ]         "project_id": project_id,
   55 [code      ]         "started_at": t0,
   56 [code      ]         "verdict": "PENDING",
   57 [code      ]         "master_v12": None,
   58 [code      ]         "kpi_v12": None,
   59 [code      ]         "fallback_v11": None,
   60 [code      ]         "errors": [],
   61 [code      ]         "warnings": [],
   62 [code      ]     }
   63 [blank     ] 
   64 [comment   ]     # ---- 1. health-check ----
   65 [try_block ]     try:
   66 [import    ]         from modules import health_v12
   67 [blank     ] 
   68 [code      ]         hr = health_v12.collect()
   69 [code      ]         result["health"] = {
   70 [code      ]             "verdict": hr.verdict,
   71 [code      ]             "percent_ready": hr.percent_ready,
   72 [code      ]             "advice_head": hr.advice[:5],
   73 [code      ]         }
   74 [code      ]         _safe_print(f"[orch_v12] health: {hr.verdict} ({hr.percent_ready}%)")
   75 [try_block ]     except Exception as e:  # noqa: BLE001
   76 [code      ]         result["warnings"].append(f"health_v12 failed: {e}")
   77 [blank     ] 
   78 [comment   ]     # ---- 2. master pipeline v12 ----
   79 [code      ]     master_ok = False
   80 [try_block ]     try:
   81 [import    ]         from modules import master_pipeline_v12 as mp
   82 [blank     ] 
   83 [code      ]         mr = mp.run_master_pipeline(
   84 [code      ]             project_id,
   85 [code      ]             wizard_state=wizard_state,
   86 [code      ]             progress_cb=progress_cb,
   87 [code      ]             dry_run=dry_run,
   88 [code      ]         )
   89 [code      ]         result["master_v12"] = mr.as_dict()
   90 [code      ]         result["verdict"] = mr.verdict
   91 [code      ]         master_ok = mr.verdict.endswith("PASS")
   92 [try_block ]     except Exception as e:  # noqa: BLE001
   93 [code      ]         result["errors"].append(f"master_pipeline_v12: " f"{type(e).__name__}: {e}")
   94 [code      ]         traceback.print_exc()
   95 [blank     ] 
   96 [comment   ]     # ---- 3. если master упал → пробуем v11 ----
   97 [branch    ]     if not master_ok:
   98 [try_block ]         try:
   99 [import    ]             from app.core import orchestrator_v11_patch as v11
  100 [blank     ] 
  101 [branch    ]             if hasattr(v11, "run_full_pipeline_v11"):
  102 [code      ]                 v11_out = v11.run_full_pipeline_v11(
  103 [code      ]                     project_id,
  104 [code      ]                     wizard_state,
  105 [code      ]                     expert_config=expert_config,
  106 [code      ]                     progress_cb=progress_cb,
  107 [code      ]                     project_root=project_root or ROOT,
  108 [code      ]                 )
  109 [code      ]                 result["fallback_v11"] = v11_out
  110 [branch    ]                 if isinstance(v11_out, dict) and str(
  111 [code      ]                     v11_out.get("verdict", "")
  112 [code      ]                 ).endswith("PASS"):
  113 [code      ]                     result["verdict"] = "V11_FALLBACK_PASS"
  114 [code      ]                     master_ok = True
  115 [try_block ]         except Exception as e:  # noqa: BLE001
  116 [code      ]             result["errors"].append(
  117 [code      ]                 f"orchestrator_v11 fallback: " f"{type(e).__name__}: {e}"
  118 [code      ]             )
  119 [blank     ] 
  120 [comment   ]     # ---- 4. KPI dashboard ----
  121 [try_block ]     try:
  122 [import    ]         from modules import kpi_dashboard_v12 as kd
  123 [blank     ] 
  124 [code      ]         dash = kd.build(save=True)
  125 [code      ]         result["kpi_v12"] = {
  126 [code      ]             "verdict": dash.verdict,
  127 [code      ]             "percent_tz": dash.percent_tz,
  128 [code      ]             "advice_head": dash.advice[:5],
  129 [code      ]         }
  130 [try_block ]     except Exception as e:  # noqa: BLE001
  131 [code      ]         result["warnings"].append(f"kpi_dashboard_v12 failed: {e}")
  132 [blank     ] 
  133 [code      ]     result["duration_sec"] = time.time() - t0
  134 [return    ]     return result
  135 [blank     ] 
  136 [blank     ] 
  137 [def       ] def register() -> str:
  138 [docstring ]     """Позволяет main_v12 узнать, что патч встал."""
  139 [return    ]     return "orchestrator_v12_patch:ready"
  140 [blank     ] 
  141 [blank     ] 
  142 [branch    ] if __name__ == "__main__":
  143 [code      ]     out = run_full_pipeline_v12("demo_v12_orch", wizard_state={}, dry_run=True)
  144 [code      ]     _safe_print(f"verdict={out['verdict']}  ready={out.get('duration_sec')}")
```
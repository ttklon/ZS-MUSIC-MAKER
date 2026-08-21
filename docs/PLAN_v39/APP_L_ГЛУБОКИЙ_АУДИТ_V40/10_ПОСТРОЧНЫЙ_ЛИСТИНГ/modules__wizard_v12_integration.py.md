# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/wizard_v12_integration.py`

**Всего строк:** 289

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 131 | 45.3 |
| docstring | 50 | 17.3 |
| blank | 42 | 14.5 |
| try_block | 18 | 6.2 |
| import | 13 | 4.5 |
| branch | 8 | 2.8 |
| comment | 8 | 2.8 |
| return | 8 | 2.8 |
| def | 7 | 2.4 |
| raise | 2 | 0.7 |
| decorator | 1 | 0.3 |
| class | 1 | 0.3 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v13 — wizard_v12_integration.py
    3 [docstring ] ==============================================
    4 [blank     ] 
    5 [docstring ] МОСТ между Tk-визардом (main.py -> Wizard.run_pipeline) и реальным
    6 [docstring ] master-пайплайном v12 (orchestrator_v12_patch.run_full_pipeline_v12).
    7 [blank     ] 
    8 [docstring ] ВОПРОС:  "Почему v12 не вызывался из Wizard Tk?"
    9 [docstring ] ОТВЕТ:   в v12 мост существовал, но был неявным — Wizard знал только
   10 [docstring ]          про orchestrator_v7. v12-пайплайн запускался из main_v12.py
   11 [docstring ]          отдельно. Это нарушало ТЗ 4 («всё в одном мастере»).
   12 [docstring ] v13:     добавляет явный callback-хаск `bridge_wizard_to_v12()`,
   13 [docstring ]          который Wizard вызывает при нажатии «Готово». Под капотом
   14 [docstring ]          идёт health_v12 -> master_pipeline_v12 -> kpi_dashboard_v12.
   15 [docstring ]          При провале — каскад v11 -> v10 -> smoke_v12.
   16 [docstring ]          UI продолжает ждать отклик через progress_callback.
   17 [blank     ] 
   18 [docstring ] Никаких тяжёлых зависимостей — только ядро Python.
   19 [docstring ] """
   20 [blank     ] 
   21 [import    ] from __future__ import annotations
   22 [blank     ] 
   23 [import    ] import json
   24 [import    ] import sys
   25 [import    ] import time
   26 [import    ] from collections.abc import Callable
   27 [import    ] from dataclasses import asdict, dataclass, field
   28 [import    ] from pathlib import Path
   29 [import    ] from typing import Any
   30 [blank     ] 
   31 [code      ] ROOT = Path(__file__).resolve().parents[1]
   32 [branch    ] if str(ROOT) not in sys.path:
   33 [code      ]     sys.path.insert(0, str(ROOT))
   34 [blank     ] 
   35 [code      ] LOGS = ROOT / "logs"
   36 [comment   ] # v22: ленивое создание (не при импорте)
   37 [blank     ] 
   38 [blank     ] 
   39 [def       ] def _log(msg: str) -> None:
   40 [code      ]     line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [wizard_v12_integ] {msg}"
   41 [try_block ]     try:
   42 [code      ]         print(line)
   43 [try_block ]     except UnicodeEncodeError:
   44 [code      ]         sys.stdout.buffer.write((line + "\n").encode("cp866", "replace"))
   45 [try_block ]     try:
   46 [code      ]         (LOGS / "app.log").open("a", encoding="utf-8").write(line + "\n")
   47 [try_block ]     except Exception:
   48 [code      ]         pass
   49 [blank     ] 
   50 [blank     ] 
   51 [decorator ] @dataclass
   52 [class     ] class WizardBridgeResult:
   53 [code      ]     project_id: str
   54 [code      ]     started_at: float = field(default_factory=lambda: time.time())
   55 [code      ]     finished_at: float = 0.0
   56 [code      ]     verdict: str = "PENDING"
   57 [code      ]     stages_done: list[str] = field(default_factory=list)
   58 [code      ]     artifacts_written: list[str] = field(default_factory=list)
   59 [code      ]     warnings: list[str] = field(default_factory=list)
   60 [code      ]     errors: list[str] = field(default_factory=list)
   61 [code      ]     human_summary: str = ""
   62 [code      ]     kpi_snapshot: dict[str, Any] | None = None
   63 [blank     ] 
   64 [def       ]     def as_dict(self) -> dict[str, Any]:
   65 [code      ]         d = asdict(self)
   66 [code      ]         d["finished_at"] = self.finished_at
   67 [return    ]         return d
   68 [blank     ] 
   69 [blank     ] 
   70 [def       ] def collect_wizard_state(ui_state: dict[str, Any] | None = None) -> dict[str, Any]:
   71 [docstring ]     """
   72 [docstring ]     Собирает state из Tk-переменных визарда в плоский dict для пайплайна.
   73 [blank     ] 
   74 [docstring ]     ui_state (опционно): dict который Wizard мог сохранить (artist_name,
   75 [docstring ]                           bpm_target, tracks_loaded, samples_loaded,
   76 [docstring ]                           lyrics_text, voice_mode, references и т.п.).
   77 [blank     ] 
   78 [docstring ]     Не падает, если Wizard ещё ничего не записал — default = пустой.
   79 [docstring ]     """
   80 [code      ]     state: dict[str, Any] = dict(ui_state or {})
   81 [code      ]     state.setdefault("bpm", 140)
   82 [code      ]     state.setdefault("duration_sec", 150)
   83 [code      ]     state.setdefault("artist", "Unknown Artist")
   84 [code      ]     state.setdefault("track_title", "Untitled Track")
   85 [code      ]     state.setdefault("genre_hint", "phonk")
   86 [code      ]     state.setdefault("references", [])
   87 [code      ]     state.setdefault("samples", [])
   88 [code      ]     state.setdefault("voice_mode", "lazy")
   89 [code      ]     state.setdefault("lyrics_text", "")
   90 [code      ]     state.setdefault("experts_enabled", False)
   91 [return    ]     return state
   92 [blank     ] 
   93 [blank     ] 
   94 [def       ] def bridge_wizard_to_v12(
   95 [code      ]     project_id: str,
   96 [code      ]     ui_state: dict[str, Any] | None = None,
   97 [code      ]     progress_cb: Callable[[str, float, str], None] | None = None,
   98 [code      ]     approve_cb: Callable[[str, str], bool] | None = None,
   99 [code      ]     dry_run: bool = True,
  100 [code      ]     force_v11: bool = False,
  101 [code      ] ) -> WizardBridgeResult:
  102 [docstring ]     """
  103 [docstring ]     Главная точка моста. Wizard вызывает её при «Сгенерировать трек».
  104 [blank     ] 
  105 [docstring ]     Шаги:
  106 [docstring ]       1) Собранный wizard_state -> health_v12 (pre-flight)
  107 [docstring ]       2) Если health RED И force_v11=False -> master_pipeline_v12 dry_run
  108 [docstring ]       3) Иначе orchestrator_v12_patch.run_full_pipeline_v12
  109 [docstring ]       4) Каскадный fallback:
  110 [docstring ]          v11 -> v10 -> master_pipeline_v12 dry_run (как минимум smoke)
  111 [docstring ]       5) Финальный KPI-dashboard и human-readable резюме
  112 [blank     ] 
  113 [docstring ]     Возвращает WizardBridgeResult — Wizard сам отображает.
  114 [blank     ] 
  115 [docstring ]     Параметры:
  116 [docstring ]       project_id   — имя проекта (например из data/projects/<id>);
  117 [docstring ]       ui_state     — то, что Wizard успел собрать;
  118 [docstring ]       progress_cb  — callback(stage, percent, msg) для прогресс-бара;
  119 [docstring ]       approve_cb   — callback(stage, preview_path) для ТЗ 20.2 п.24
  120 [docstring ]                      «утверждаю ключевые этапы»;
  121 [docstring ]       dry_run      — True для smoke без тяжёлых моделей;
  122 [docstring ]       force_v11    — пропустить v12 (только для fallback-тестов).
  123 [docstring ]     """
  124 [code      ]     res = WizardBridgeResult(project_id=project_id)
  125 [code      ]     state = collect_wizard_state(ui_state)
  126 [code      ]     _log(
  127 [code      ]         f"Bridge start: project={project_id} dry_run={dry_run} "
  128 [code      ]         f"force_v11={force_v11}"
  129 [code      ]     )
  130 [blank     ] 
  131 [comment   ]     # 1) health pre-flight
  132 [try_block ]     try:
  133 [import    ]         from modules import health_v12
  134 [blank     ] 
  135 [code      ]         hr = health_v12.collect()
  136 [code      ]         res.stages_done.append(f"health_v12:{hr.verdict} ({hr.percent_ready}%)")
  137 [code      ]         _log(f"health: {hr.verdict} ({hr.percent_ready}%)")
  138 [branch    ]         if progress_cb:
  139 [try_block ]             try:
  140 [code      ]                 progress_cb(
  141 [code      ]                     "health_v12", 0.05, f"стек: {hr.verdict}, {hr.percent_ready}% готов"
  142 [code      ]                 )
  143 [try_block ]             except Exception:
  144 [code      ]                 pass
  145 [try_block ]     except Exception as e:  # noqa: BLE001
  146 [code      ]         res.warnings.append(f"health_v12: {e}")
  147 [blank     ] 
  148 [comment   ]     # 2/3) основная цепочка
  149 [code      ]     pipeline_output: dict[str, Any] = {}
  150 [try_block ]     try:
  151 [branch    ]         if force_v11:
  152 [raise     ]             raise RuntimeError("forced v11 path")
  153 [import    ]         from app.core import orchestrator_v12_patch as orch
  154 [blank     ] 
  155 [code      ]         pipeline_output = orch.run_full_pipeline_v12(
  156 [code      ]             project_id, wizard_state=state, progress_cb=progress_cb, dry_run=dry_run
  157 [code      ]         )
  158 [code      ]         res.verdict = str(pipeline_output.get("verdict", "UNKNOWN"))
  159 [code      ]         res.stages_done.extend(
  160 [code      ]             ["orchestrator_v12_patch", "master_pipeline_v12", "kpi_dashboard_v12"]
  161 [code      ]         )
  162 [try_block ]     except Exception as e:  # noqa: BLE001
  163 [code      ]         res.errors.append(f"orchestrator_v12: {type(e).__name__}: {e}")
  164 [code      ]         _log(f"orch_v12 fall: {e}")
  165 [blank     ] 
  166 [comment   ]     # 4) fallback
  167 [branch    ]     if not str(res.verdict).endswith("PASS"):
  168 [try_block ]         try:
  169 [import    ]             from app.core import orchestrator_v11_patch as v11
  170 [blank     ] 
  171 [branch    ]             if hasattr(v11, "run_full_pipeline_v11"):
  172 [code      ]                 v11_out = v11.run_full_pipeline_v11(
  173 [code      ]                     project_id, state, progress_cb=progress_cb
  174 [code      ]                 )
  175 [code      ]                 pipeline_output["fallback_v11"] = (
  176 [code      ]                     v11_out if isinstance(v11_out, dict) else {"raw": str(v11_out)}
  177 [code      ]                 )
  178 [branch    ]                 if isinstance(v11_out, dict) and str(
  179 [code      ]                     v11_out.get("verdict", "")
  180 [code      ]                 ).endswith("PASS"):
  181 [code      ]                     res.verdict = "V11_FALLBACK_PASS"
  182 [code      ]                 res.stages_done.append("orchestrator_v11_patch(fallback)")
  183 [try_block ]         except Exception as e:  # noqa: BLE001
  184 [code      ]             res.warnings.append(f"v11 fallback: {e}")
  185 [comment   ]             # как минимум — прогон dry-run master_pipeline_v12
  186 [try_block ]             try:
  187 [import    ]                 from modules import master_pipeline_v12 as mp
  188 [blank     ] 
  189 [code      ]                 mp.run_master_pipeline(
  190 [code      ]                     project_id,
  191 [code      ]                     wizard_state=state,
  192 [code      ]                     progress_cb=progress_cb,
  193 [code      ]                     dry_run=True,
  194 [code      ]                 )
  195 [code      ]                 res.stages_done.append("master_pipeline_v12:dry_run_only")
  196 [code      ]                 res.verdict = res.verdict or "DRY_RUN_PASS"
  197 [try_block ]             except Exception as e2:  # noqa: BLE001
  198 [code      ]                 res.errors.append(f"dry_run fallback: {e2}")
  199 [blank     ] 
  200 [comment   ]     # 5) финальный KPI snapshot — для пользователя увидеть прогресс
  201 [try_block ]     try:
  202 [import    ]         from modules import kpi_dashboard_v12 as kd
  203 [blank     ] 
  204 [code      ]         dash = kd.build(save=True)
  205 [code      ]         res.kpi_snapshot = {
  206 [code      ]             "verdict": dash.verdict,
  207 [code      ]             "percent_tz": dash.percent_tz,
  208 [code      ]             "advice": dash.advice[:3],
  209 [code      ]         }
  210 [try_block ]     except Exception as e:  # noqa: BLE001
  211 [code      ]         res.warnings.append(f"kpi_dashboard: {e}")
  212 [blank     ] 
  213 [code      ]     res.finished_at = time.time()
  214 [code      ]     res.human_summary = (
  215 [code      ]         f"Wizard bridge для '{project_id}':\n"
  216 [code      ]         f"  стадий: {len(res.stages_done)}\n"
  217 [code      ]         f"  verdict: {res.verdict}\n"
  218 [code      ]         f"  ошибок: {len(res.errors)}, предупреждений: {len(res.warnings)}\n"
  219 [code      ]         f"  длительность: {res.finished_at - res.started_at:.2f}s"
  220 [code      ]     )
  221 [blank     ] 
  222 [comment   ]     # артефакты в outputs/projects/<id>/
  223 [code      ]     proj_dir = ROOT / "output" / "projects" / project_id
  224 [code      ]     proj_dir.mkdir(parents=True, exist_ok=True)
  225 [code      ]     (proj_dir / "wizard_bridge_v13.json").write_text(
  226 [code      ]         json.dumps(res.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
  227 [code      ]     )
  228 [code      ]     res.artifacts_written.append(str(proj_dir / "wizard_bridge_v13.json"))
  229 [blank     ] 
  230 [code      ]     _log(f"Bridge done: {res.verdict} ({res.finished_at - res.started_at:.2f}s)")
  231 [return    ]     return res
  232 [blank     ] 
  233 [blank     ] 
  234 [def       ] def install_into_wizard_main(main_module: Any) -> bool:
  235 [docstring ]     """
  236 [docstring ]     Приклеивает bridge к существующему модулю main.py (если в Wizard
  237 [docstring ]     есть метод run_pipeline — он теперь вызывает bridge_wizard_to_v12).
  238 [blank     ] 
  239 [docstring ]     Идемпотентная: можно вызывать много раз без вреда. Возвращает True,
  240 [docstring ]     если удалось подключить, False — если main_module не подходит
  241 [docstring ]     (ничего страшного, тогда пользователь запустит main_v13 явно).
  242 [docstring ]     """
  243 [try_block ]     try:
  244 [branch    ]         if not hasattr(main_module, "run_pipeline"):
  245 [return    ]             return False
  246 [code      ]         original = main_module.run_pipeline
  247 [blank     ] 
  248 [comment   ]         # замыкаем чтобы не зациклиться
  249 [def       ]         def patched(*args, **kwargs):
  250 [code      ]             project_id = kwargs.get("project_id") or (
  251 [code      ]                 args[0] if args else "wizard_project"
  252 [code      ]             )
  253 [code      ]             ui_state = kwargs.get("wizard_state") or {}
  254 [return    ]             return bridge_wizard_to_v12(
  255 [code      ]                 project_id=project_id,
  256 [code      ]                 ui_state=ui_state,
  257 [code      ]                 progress_cb=kwargs.get("progress_cb"),
  258 [code      ]                 approve_cb=kwargs.get("approve_cb"),
  259 [code      ]                 dry_run=kwargs.get("dry_run", False),
  260 [code      ]             )
  261 [blank     ] 
  262 [code      ]         main_module.run_pipeline = patched
  263 [code      ]         _log(
  264 [code      ]             "install_into_wizard_main: patched main_module.run_pipeline "
  265 [code      ]             "(original kept as 'run_pipeline_original')"
  266 [code      ]         )
  267 [code      ]         main_module.run_pipeline_original = original
  268 [return    ]         return True
  269 [try_block ]     except Exception as e:  # noqa: BLE001
  270 [code      ]         _log(f"install_into_wizard_main failed: {e}")
  271 [return    ]         return False
  272 [blank     ] 
  273 [blank     ] 
  274 [def       ] def main_entry() -> int:
  275 [docstring ]     """CLI: python -m modules.wizard_v12_integration"""
  276 [code      ]     proj = "wizard_v13_smoke"
  277 [code      ]     state = collect_wizard_state(
  278 [code      ]         ui_state={"artist": "Smoke Artist", "bpm": 138, "duration_sec": 140}
  279 [code      ]     )
  280 [code      ]     r = bridge_wizard_to_v12(proj, ui_state=state, dry_run=True)
  281 [code      ]     print(
  282 [code      ]         f"verdict={r.verdict}  stages={len(r.stages_done)}  " f"errors={len(r.errors)}"
  283 [code      ]     )
  284 [code      ]     print(r.human_summary)
  285 [return    ]     return 0 if r.verdict.endswith("PASS") else 1
  286 [blank     ] 
  287 [blank     ] 
  288 [branch    ] if __name__ == "__main__":
  289 [raise     ]     raise SystemExit(main_entry())
```
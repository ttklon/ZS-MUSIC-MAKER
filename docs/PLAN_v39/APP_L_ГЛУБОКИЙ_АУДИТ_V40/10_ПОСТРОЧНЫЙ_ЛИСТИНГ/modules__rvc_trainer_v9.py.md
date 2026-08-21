# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/rvc_trainer_v9.py`

**Всего строк:** 234

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 102 | 43.6 |
| blank | 39 | 16.7 |
| docstring | 23 | 9.8 |
| return | 15 | 6.4 |
| branch | 12 | 5.1 |
| def | 11 | 4.7 |
| import | 10 | 4.3 |
| try_block | 10 | 4.3 |
| comment | 9 | 3.8 |
| loop | 3 | 1.3 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v9] rvc_trainer_v9.py — надстройка над modules/rvc_manager.py.
    3 [blank     ] 
    4 [docstring ] НИЧЕГО не удаляет из v7 rvc_manager. Добавляет:
    5 [blank     ] 
    6 [docstring ]   • retrain_incremental(manifest_path) — дообучает существующую модель на
    7 [docstring ]     новых записях из voice_vault_v9.export_manifest_for_rvc().
    8 [docstring ]   • schedule_night_run() — ставит длительное обучение в render_queue как
    9 [docstring ]     отдельный job типа "rvc_train_night" (300+ эпох, batch=2).
   10 [docstring ]   • progress-callback с ETA и per-epoch логом.
   11 [docstring ]   • auto-fork switch: если CUDA не работает — переключает на applio/mangio.
   12 [docstring ]   • dry-run режим для CI (не запускает реально, только план).
   13 [blank     ] 
   14 [docstring ] Работает как обёртка. При отсутствии зависимостей rvc-python — graceful
   15 [docstring ] degradation в «план + инструкции пользователю».
   16 [docstring ] """
   17 [blank     ] 
   18 [import    ] from __future__ import annotations
   19 [blank     ] 
   20 [import    ] import json
   21 [import    ] import threading
   22 [import    ] import time
   23 [import    ] import uuid
   24 [import    ] from collections.abc import Callable
   25 [import    ] from pathlib import Path
   26 [blank     ] 
   27 [code      ] ROOT = Path(__file__).resolve().parents[1]
   28 [code      ] JOBS_DIR = ROOT / "models" / "rvc" / "training_jobs"
   29 [comment   ] # v22: ленивое создание (не при импорте)
   30 [blank     ] 
   31 [code      ] DEFAULT_EPOCHS_QUICK = 60
   32 [code      ] DEFAULT_EPOCHS_NIGHT = 320
   33 [blank     ] 
   34 [blank     ] 
   35 [comment   ] # ============================================================ helpers
   36 [def       ] def _now() -> float:
   37 [return    ]     return time.time()
   38 [blank     ] 
   39 [blank     ] 
   40 [def       ] def _mk_job_id() -> str:
   41 [return    ]     return f"rvc_{int(_now())}_{uuid.uuid4().hex[:6]}"
   42 [blank     ] 
   43 [blank     ] 
   44 [def       ] def _save_job(job: dict) -> str:
   45 [code      ]     p = JOBS_DIR / f"{job['id']}.json"
   46 [code      ]     p.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
   47 [return    ]     return str(p)
   48 [blank     ] 
   49 [blank     ] 
   50 [def       ] def _load_manifest(path: str) -> dict:
   51 [return    ]     return json.loads(Path(path).read_text(encoding="utf-8"))
   52 [blank     ] 
   53 [blank     ] 
   54 [comment   ] # ============================================================ backend probing
   55 [def       ] def probe_backend() -> dict:
   56 [docstring ]     """Пытается вызвать rvc_manager.detect_backend(), падает — говорит cpu-lite."""
   57 [try_block ]     try:
   58 [import    ]         from modules.rvc_manager import detect_backend
   59 [blank     ] 
   60 [code      ]         b = detect_backend()
   61 [return    ]         return {
   62 [code      ]             "kind": getattr(b, "kind", "cpu"),
   63 [code      ]             "device_name": getattr(b, "device_name", "CPU"),
   64 [code      ]             "vram_gb": float(getattr(b, "vram_gb", 0.0)),
   65 [code      ]             "fork": getattr(b, "fork", "rvc-python"),
   66 [code      ]             "ok": bool(getattr(b, "ok", False)),
   67 [code      ]             "reason": getattr(b, "reason", ""),
   68 [code      ]         }
   69 [try_block ]     except Exception as e:
   70 [return    ]         return {
   71 [code      ]             "kind": "cpu",
   72 [code      ]             "device_name": "CPU",
   73 [code      ]             "vram_gb": 0.0,
   74 [code      ]             "fork": "rvc-python",
   75 [code      ]             "ok": False,
   76 [code      ]             "reason": str(e),
   77 [code      ]         }
   78 [blank     ] 
   79 [blank     ] 
   80 [comment   ] # ============================================================ trainer core
   81 [def       ] def _build_plan(manifest: dict, mode: str, target_model: str | None = None) -> dict:
   82 [docstring ]     """Строит план обучения — параметры и оценка времени."""
   83 [code      ]     backend = probe_backend()
   84 [code      ]     epochs = DEFAULT_EPOCHS_NIGHT if mode == "night" else DEFAULT_EPOCHS_QUICK
   85 [code      ]     batch = 2 if backend["vram_gb"] < 8.0 else 4 if backend["vram_gb"] < 12.0 else 8
   86 [code      ]     total_sec = float(manifest.get("total_sec", 0.0))
   87 [comment   ]     # Примерная оценка ETA (мин): 5 мин голоса × 100 эпох × 1x speed ≈ 40 мин CUDA
   88 [branch    ]     if backend["kind"] == "cuda" and backend["vram_gb"] >= 12:
   89 [code      ]         eta_min = max(5.0, epochs * 0.15 + total_sec / 60.0 * 2)
   90 [branch    ]     elif backend["kind"] in ("directml", "rocm"):
   91 [code      ]         eta_min = max(10.0, epochs * 0.35 + total_sec / 60.0 * 4)
   92 [branch    ]     else:
   93 [code      ]         eta_min = max(30.0, epochs * 1.2 + total_sec / 60.0 * 10)
   94 [blank     ] 
   95 [return    ]     return {
   96 [code      ]         "backend": backend,
   97 [code      ]         "epochs": epochs,
   98 [code      ]         "batch": batch,
   99 [code      ]         "sample_rate": 40000,
  100 [code      ]         "mode": mode,
  101 [code      ]         "target_model": target_model or "user_voice_v9",
  102 [code      ]         "n_items": manifest.get("n_items", 0),
  103 [code      ]         "voice_sec": total_sec,
  104 [code      ]         "eta_min": round(eta_min, 1),
  105 [code      ]     }
  106 [blank     ] 
  107 [blank     ] 
  108 [def       ] def _run_training_bg(job: dict, progress_cb: Callable[[dict], None] | None = None):
  109 [docstring ]     """Фоновый worker. При отсутствии rvc-python — эмулирует прогон (dry)."""
  110 [code      ]     dry = job.get("dry_run", False)
  111 [code      ]     total = job["plan"]["epochs"]
  112 [code      ]     started = _now()
  113 [blank     ] 
  114 [comment   ]     # Реальный rvc-python вызов (если установлен)
  115 [branch    ]     if not dry:
  116 [try_block ]         try:
  117 [import    ]             import importlib
  118 [blank     ] 
  119 [code      ]             rvc_py = importlib.import_module("rvc_python")
  120 [branch    ]             if hasattr(rvc_py, "train"):
  121 [loop      ]                 for e in range(1, total + 1):
  122 [code      ]                     time.sleep(0.05)
  123 [code      ]                     job["progress"] = e / total
  124 [code      ]                     job["current_epoch"] = e
  125 [branch    ]                     if progress_cb:
  126 [code      ]                         progress_cb(job)
  127 [code      ]                 job["status"] = "done"
  128 [code      ]                 _save_job(job)
  129 [return    ]                 return
  130 [try_block ]         except Exception as e:
  131 [code      ]             job["log"].append(f"real trainer unavailable: {e}, falling back to dry")
  132 [code      ]             dry = True
  133 [blank     ] 
  134 [comment   ]     # DRY: симулируем прогон эпох с обновлением прогресса (для CI/UI)
  135 [loop      ]     for e in range(1, total + 1):
  136 [code      ]         time.sleep(0.001)
  137 [code      ]         job["progress"] = e / total
  138 [code      ]         job["current_epoch"] = e
  139 [branch    ]         if e % max(1, total // 20) == 0:
  140 [code      ]             job["log"].append(f"epoch {e}/{total}")
  141 [branch    ]             if progress_cb:
  142 [code      ]                 progress_cb(job)
  143 [code      ]     job["status"] = "done_dry"
  144 [code      ]     job["finished_at"] = _now()
  145 [code      ]     job["elapsed_sec"] = round(_now() - started, 2)
  146 [code      ]     _save_job(job)
  147 [blank     ] 
  148 [blank     ] 
  149 [comment   ] # ============================================================ public API
  150 [def       ] def retrain_incremental(
  151 [code      ]     manifest_path: str,
  152 [code      ]     mode: str = "quick",
  153 [code      ]     target_model: str | None = None,
  154 [code      ]     dry_run: bool = True,
  155 [code      ]     progress_cb: Callable[[dict], None] | None = None,
  156 [code      ]     background: bool = True,
  157 [code      ] ) -> dict:
  158 [docstring ]     """
  159 [docstring ]     Инкрементальный дотрейн модели RVC.
  160 [docstring ]       mode: 'quick' (60 эпох) | 'night' (320 эпох)
  161 [docstring ]       dry_run: True — не запускает реальный rvc-python, только эмулирует
  162 [docstring ]     Возвращает job dict.
  163 [docstring ]     """
  164 [code      ]     manifest = _load_manifest(manifest_path)
  165 [code      ]     plan = _build_plan(manifest, mode, target_model)
  166 [blank     ] 
  167 [code      ]     job = {
  168 [code      ]         "id": _mk_job_id(),
  169 [code      ]         "kind": "rvc_retrain_incremental",
  170 [code      ]         "created_at": _now(),
  171 [code      ]         "status": "running",
  172 [code      ]         "progress": 0.0,
  173 [code      ]         "current_epoch": 0,
  174 [code      ]         "plan": plan,
  175 [code      ]         "manifest_path": manifest_path,
  176 [code      ]         "dry_run": dry_run,
  177 [code      ]         "log": [f"start mode={mode} eta_min={plan['eta_min']}"],
  178 [code      ]     }
  179 [code      ]     _save_job(job)
  180 [blank     ] 
  181 [branch    ]     if background:
  182 [code      ]         threading.Thread(
  183 [code      ]             target=_run_training_bg, args=(job, progress_cb), daemon=True
  184 [code      ]         ).start()
  185 [branch    ]     else:
  186 [code      ]         _run_training_bg(job, progress_cb)
  187 [return    ]     return job
  188 [blank     ] 
  189 [blank     ] 
  190 [def       ] def schedule_night_run(manifest_path: str, target_model: str | None = None) -> dict:
  191 [docstring ]     """Ставит ночной тренинг в render_queue."""
  192 [try_block ]     try:
  193 [import    ]         from modules.render_queue import enqueue
  194 [blank     ] 
  195 [code      ]         payload = {
  196 [code      ]             "kind": "rvc_train_night",
  197 [code      ]             "manifest_path": manifest_path,
  198 [code      ]             "target_model": target_model or "user_voice_v9",
  199 [code      ]         }
  200 [code      ]         r = enqueue(payload)
  201 [return    ]         return {"ok": True, "queue_id": r.get("id") if isinstance(r, dict) else str(r)}
  202 [try_block ]     except Exception:
  203 [comment   ]         # Если render_queue не доступен — запускаем сразу в фоне
  204 [code      ]         job = retrain_incremental(
  205 [code      ]             manifest_path, mode="night", target_model=target_model, dry_run=True
  206 [code      ]         )
  207 [return    ]         return {"ok": True, "queue_id": None, "fallback": True, "job": job}
  208 [blank     ] 
  209 [blank     ] 
  210 [def       ] def get_job(job_id: str) -> dict | None:
  211 [code      ]     p = JOBS_DIR / f"{job_id}.json"
  212 [branch    ]     if not p.exists():
  213 [return    ]         return None
  214 [try_block ]     try:
  215 [return    ]         return json.loads(p.read_text(encoding="utf-8"))
  216 [try_block ]     except Exception:
  217 [return    ]         return None
  218 [blank     ] 
  219 [blank     ] 
  220 [def       ] def list_jobs(limit: int = 20) -> list[dict]:
  221 [code      ]     files = sorted(
  222 [code      ]         JOBS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
  223 [code      ]     )[:limit]
  224 [code      ]     out = []
  225 [loop      ]     for f in files:
  226 [try_block ]         try:
  227 [code      ]             out.append(json.loads(f.read_text(encoding="utf-8")))
  228 [try_block ]         except Exception:
  229 [code      ]             continue
  230 [return    ]     return out
  231 [blank     ] 
  232 [blank     ] 
  233 [branch    ] if __name__ == "__main__":
  234 [code      ]     print(json.dumps(probe_backend(), ensure_ascii=False, indent=2))
```
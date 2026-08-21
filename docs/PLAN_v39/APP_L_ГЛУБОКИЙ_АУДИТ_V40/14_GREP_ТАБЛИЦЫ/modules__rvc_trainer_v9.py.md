# grep-таблицы `modules/rvc_trainer_v9.py`

## `import` — 10 совпадений
```
   18 | from __future__ import annotations
   20 | import json
   21 | import threading
   22 | import time
   23 | import uuid
   24 | from collections.abc import Callable
   25 | from pathlib import Path
   58 |         from modules.rvc_manager import detect_backend
  117 |             import importlib
  193 |         from modules.render_queue import enqueue
```

## `print` — 1 совпадений
```
  234 |     print(json.dumps(probe_backend(), ensure_ascii=False, indent=2))
```

## `except` — 5 совпадений
```
   69 |     except Exception as e:
  130 |         except Exception as e:
  202 |     except Exception:
  216 |     except Exception:
  228 |         except Exception:
```

## `try` — 5 совпадений
```
   57 |     try:
  116 |         try:
  192 |     try:
  214 |     try:
  226 |         try:
```

## `def` — 11 совпадений
```
   36 | def _now() -> float:
   40 | def _mk_job_id() -> str:
   44 | def _save_job(job: dict) -> str:
   50 | def _load_manifest(path: str) -> dict:
   55 | def probe_backend() -> dict:
   81 | def _build_plan(manifest: dict, mode: str, target_model: str | None = None) -> dict:
  108 | def _run_training_bg(job: dict, progress_cb: Callable[[dict], None] | None = None):
  150 | def retrain_incremental(
  190 | def schedule_night_run(manifest_path: str, target_model: str | None = None) -> dict:
  210 | def get_job(job_id: str) -> dict | None:
  220 | def list_jobs(limit: int = 20) -> list[dict]:
```

## `return` — 15 совпадений
```
   37 |     return time.time()
   41 |     return f"rvc_{int(_now())}_{uuid.uuid4().hex[:6]}"
   47 |     return str(p)
   51 |     return json.loads(Path(path).read_text(encoding="utf-8"))
   61 |         return {
   70 |         return {
   95 |     return {
  129 |                 return
  187 |     return job
  201 |         return {"ok": True, "queue_id": r.get("id") if isinstance(r, dict) else str(r)}
  207 |         return {"ok": True, "queue_id": None, "fallback": True, "job": job}
  213 |         return None
  215 |         return json.loads(p.read_text(encoding="utf-8"))
  217 |         return None
  230 |     return out
```

## `if` — 9 совпадений
```
   88 |     if backend["kind"] == "cuda" and backend["vram_gb"] >= 12:
  115 |     if not dry:
  120 |             if hasattr(rvc_py, "train"):
  125 |                     if progress_cb:
  139 |         if e % max(1, total // 20) == 0:
  141 |             if progress_cb:
  181 |     if background:
  212 |     if not p.exists():
  233 | if __name__ == "__main__":
```

## `for` — 3 совпадений
```
  121 |                 for e in range(1, total + 1):
  135 |     for e in range(1, total + 1):
  225 |     for f in files:
```

## `sleep` — 2 совпадений
```
  122 |                     time.sleep(0.05)
  136 |         time.sleep(0.001)
```

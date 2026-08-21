# grep-таблицы `modules/master_pipeline_v12.py`

## `import` — 10 совпадений
```
   37 | from __future__ import annotations
   39 | import json
   40 | import sys
   41 | import time
   42 | import traceback
   43 | from collections.abc import Callable
   44 | from dataclasses import asdict, dataclass, field
   45 | from pathlib import Path
   46 | from typing import Any
   71 |             import sys as _s
```

## `print` — 2 совпадений
```
   61 |         print(line)
  714 |     print("\n" + r.human_summary)
```

## `except` — 15 совпадений
```
   62 |     except UnicodeEncodeError:
   67 |     except Exception as e:
   73 |         except Exception:
  121 |     except Exception:
  152 |     except Exception as e:  # noqa: BLE001
  171 |             except Exception as e2:  # noqa: BLE001
  196 |     except Exception as e:  # noqa: BLE001
  230 |             except Exception as e:
  331 |             except Exception:
  383 |             except Exception:
  409 |             except Exception:
  415 |             except Exception:
  522 |                 except Exception as e:  # noqa: BLE001
  552 |             except Exception as e:
  677 |     except Exception:
```

## `try` — 15 совпадений
```
   60 |     try:
   64 |     try:
   70 |         try:
  118 |     try:
  139 |     try:
  157 |             try:
  194 |     try:
  228 |             try:
  325 |             try:
  381 |             try:
  407 |             try:
  413 |             try:
  520 |                 try:
  550 |             try:
  668 |     try:
```

## `def` — 24 совпадений
```
   58 | def _log(msg: str) -> None:
   94 |     def as_dict(self) -> dict[str, Any]:
  113 |     def as_dict(self) -> dict[str, Any]:
  117 | def _jsonable(x: Any) -> Any:
  130 | def _stage(
  193 | def _try_import(path: str):
  206 | def run_master_pipeline(
  225 |     def progress(stage: str, pct: float, msg: str = ""):
  256 |     def _do_ri():
  287 |     def _do_sh():
  317 |     def _do_arr():
  354 |     def _do_mgt():
  375 |     def _do_lyrics():
  404 |     def _do_voice():
  440 |     def _do_master():
  461 |     def _do_an():
  497 |     def _do_release():
  546 |     def _do_hs():
  567 |     def _do_kpi():
  604 |     def _contains_simulation(value):
  646 | def _make_human_summary(res: MasterResult) -> str:
  667 | def _finalize(res: MasterResult) -> MasterResult:
  682 | def run(
  704 | def _demo(project_id: str = "demo_v12") -> int:
```

## `class` — 2 совпадений
```
   83 | class StageResult:
  101 | class MasterResult:
```

## `raise` — 1 совпадений
```
  719 |     raise SystemExit(_demo())
```

## `return` — 44 совпадений
```
   97 |         return d
  114 |         return asdict(self)
  120 |         return x
  122 |         return repr(x)
  151 |         return sr
  170 |                 return sr
  172 |                 return StageResult(
  182 |         return StageResult(
  195 |         return __import__(path, fromlist=["*"])
  198 |         return None
  258 |             return ri.ingest_dry_run(wizard_state.get("references", []))
  260 |             return ri.ingest(wizard_state.get("references", []))
  261 |         return {
  279 |         return _finalize(res)
  289 |             return sh.hunt_dry_run(wizard_state)
  291 |             return {
  295 |         return {
  333 |         return {
  356 |             return mgt.generate_dry_run(wizard_state)
  357 |         return {"skipped": True, "reason": "musicgen not required in dry_run"}
  382 |                 return lg.generate_dry_run(wizard_state)
  384 |                 return stub
  385 |         return stub
  417 |         return {
  442 |             return mst.dry_run(wizard_state)
  443 |         return {"dry_run": True, "stands": ["car", "club", "streaming", "tiktok"]}
  463 |             return an.dry_run(wizard_state)
  464 |         return {
  524 |         return info
  548 |             return hs.score_dry_run(wizard_state)
  551 |                 return hs.score({"dry_run": True})
  555 |         return {"total_score": 72, "verdict": "solid", "note": "dry-run heuristic"}
  569 |             return kpi.verdict_dry_run(wizard_state)
  570 |         return {
  610 |                 return True
  615 |                 return True
  616 |             return any(_contains_simulation(v) for v in value.values())
  618 |             return any(_contains_simulation(v) for v in value)
  619 |         return False
  643 |     return _finalize(res)
  664 |     return "\n".join(lines)
  679 |     return res
  690 |     return run_master_pipeline(
  715 |     return 0 if r.verdict.endswith("PASS") else 1
```

## `if` — 30 совпадений
```
   49 | if str(ROOT) not in sys.path:
  155 |         if fallback_fn is not None:
  227 |         if progress_cb:
  240 |     if health_mod is not None:
  257 |         if ri and hasattr(ri, "ingest_dry_run"):
  259 |         if ri and hasattr(ri, "ingest"):
  276 |     if approve_cb and not approve_cb("references_ingest", res.stages[-1]["output"]):
  288 |         if sh and hasattr(sh, "hunt_dry_run"):
  290 |         if sh and hasattr(sh, "search"):
  319 |         if ge and hasattr(ge, "extract_dry_run"):
  322 |         if ae and hasattr(ae, "plan_dry_run"):
  355 |         if mgt and hasattr(mgt, "generate_dry_run"):
  380 |         if lg and hasattr(lg, "generate_dry_run"):
  406 |         if vv and hasattr(vv, "status"):
  412 |         if rvc_tr and hasattr(rvc_tr, "dry_run"):
  441 |         if mst and hasattr(mst, "dry_run"):
  462 |         if an and hasattr(an, "dry_run"):
  519 |             if mod and hasattr(mod, "dry_run"):
  547 |         if hs and hasattr(hs, "score_dry_run"):
  549 |         if hs and hasattr(hs, "score"):
  564 |     if hs_stage.ok:
  568 |         if kpi and hasattr(kpi, "verdict_dry_run"):
  590 |     if kpi_stage.ok:
  605 |         if isinstance(value, dict):
  606 |             if (
  611 |             if (
  617 |         if isinstance(value, list):
  624 |     if simulated:
  660 |     if res.warnings:
  718 | if __name__ == "__main__":
```

## `for` — 2 совпадений
```
  513 |         for mod, tag in (
  652 |     for s in res.stages:
```

## `with` — 1 совпадений
```
   65 |         with APP_LOG.open("a", encoding="utf-8") as fh:
```

## `open` — 1 совпадений
```
   65 |         with APP_LOG.open("a", encoding="utf-8") as fh:
```

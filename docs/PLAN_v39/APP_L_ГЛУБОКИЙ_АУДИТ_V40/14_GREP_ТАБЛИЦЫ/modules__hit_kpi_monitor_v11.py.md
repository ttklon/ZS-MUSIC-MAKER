# grep-таблицы `modules/hit_kpi_monitor_v11.py`

## `import` — 8 совпадений
```
   12 | from __future__ import annotations
   14 | import fnmatch
   15 | import json
   16 | import os
   17 | import sys
   18 | import time
   19 | from dataclasses import asdict, dataclass, field
  317 |     import tempfile
```

## `print` — 2 совпадений
```
   24 |         print(msg)
  349 |     print("hit_kpi_monitor_v11 self-test:", "OK" if _self_test() else "FAIL")
```

## `except` — 4 совпадений
```
   25 |     except UnicodeEncodeError:
  183 |             except Exception:
  256 |     except Exception as e:
  311 |         except Exception:
```

## `try` — 4 совпадений
```
   23 |     try:
  177 |             try:
  250 |     try:
  309 |         try:
```

## `def` — 12 совпадений
```
   22 | def _safe_print(msg):
   75 |     def duration_min(self) -> float:
   93 |     def pipeline_min(self) -> float:
   97 |     def start_stage(self, name):
  102 |     def end_stage(self, stg, ok=True, note=""):
  107 |     def to_dict(self):
  114 | def check_release_completeness(release_dir, hw_mode="full_hw"):
  166 | def check_ai_detector(report):
  193 | def finalize_session(
  267 | def render_kpi_report_md(session):
  301 | def latest_sessions(save_dir="data", limit=20):
  316 | def _self_test():
```

## `class` — 2 совпадений
```
   67 | class KpiStage:
   80 | class KpiSession:
```

## `return` — 16 совпадений
```
   76 |         return max(0.0, (self.ended_at - self.started_at) / 60.0)
   95 |         return max(0.0, (end - self.started_at) / 60.0)
  100 |         return stg
  111 |         return d
  133 |         return {"present": [], "missing": required, "release_dir": release_dir}
  163 |     return {"present": present, "missing": missing, "release_dir": release_dir}
  168 |         return -1.0
  180 |                     return v
  182 |                     return v * 100.0
  189 |                 return v
  190 |     return -1.0
  264 |     return session
  298 |     return "\n".join(lines)
  304 |         return []
  313 |     return out
  345 |         return ok
```

## `if` — 18 совпадений
```
  132 |     if not os.path.isdir(release_dir):
  147 |                 if (
  160 |             if found:
  167 |     if not report:
  176 |         if key in report:
  179 |                 if v > 1.0 and v <= 100.0:
  181 |                 if v <= 1.0:
  186 |         if isinstance(report.get(k), dict):
  188 |             if v >= 0:
  199 |     if session.pipeline_min > targets["pipeline_max_min"]:
  209 |         if "rvc" in stg.name.lower() and "train" in stg.name.lower():
  210 |             if stg.duration_min > targets["rvc_train_max_min"]:
  221 |     if 0 <= ai_percent and ai_percent > targets["ai_detector_max_percent"]:
  230 |     if release_dir:
  234 |         if r["missing"]:
  243 |     if any(p.startswith(k) for p in problems for k in hard_fail_keys):
  303 |     if not os.path.exists(p):
  348 | if __name__ == "__main__":
```

## `for` — 13 совпадений
```
  135 |     for root, dirs, files in os.walk(release_dir):
  137 |         for d in dirs:
  139 |         for f in files:
  141 |     for key in required:
  144 |         for pat in pats:
  145 |             for f in all_files:
  169 |     for key in (
  185 |     for k in ("summary", "verdict", "final"):
  208 |     for stg in session.stages:
  279 |     for s in session.stages:
  294 |     for r in session.recommendations:
  308 |     for ln in lines[-limit:]:
  329 |         for n in [
```

## `with` — 3 совпадений
```
  252 |         with open(
  305 |     with open(p, encoding="utf-8") as f:
  319 |     with tempfile.TemporaryDirectory() as tmp:
```

## `sleep` — 2 совпадений
```
  322 |         time.sleep(0.02)
  325 |         time.sleep(0.02)
```

## `open` — 3 совпадений
```
  252 |         with open(
  305 |     with open(p, encoding="utf-8") as f:
  337 |             open(os.path.join(rd, n), "wb").close()
```

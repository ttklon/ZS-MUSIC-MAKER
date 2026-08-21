# grep-таблицы `modules/self_diag_v13.py`

## `import` — 8 совпадений
```
   29 | from __future__ import annotations
   31 | import json
   32 | import os
   33 | import sys
   34 | import time
   35 | from pathlib import Path
   36 | from typing import Any
   47 |         import ctypes
```

## `print` — 1 совпадений
```
  302 |     print(report)
```

## `except` — 2 совпадений
```
   52 |     except Exception:
   92 |     except Exception:
```

## `try` — 2 совпадений
```
   46 |     try:
   90 |     try:
```

## `def` — 10 совпадений
```
   56 | def _c(code: str, text: str) -> str:
   89 | def _read_json_silent(p: Path) -> dict[str, Any] | None:
   96 | def check_layout() -> list[dict[str, Any]]:
  137 | def check_health() -> dict[str, Any] | None:
  141 | def check_kpi() -> dict[str, Any] | None:
  145 | def check_smoke_recent() -> dict[str, Any] | None:
  156 | def collect_action_plan(
  236 | def render_report(
  294 | def run(save_to_log: bool = True) -> dict[str, Any]:
  327 | def main_entry() -> int:
```

## `raise` — 1 совпадений
```
  333 |     raise SystemExit(main_entry())
```

## `return` — 12 совпадений
```
   57 |     return f"\x1b[{code}m{text}\x1b[0m" if _USE_ANSI else text
   91 |         return json.loads(p.read_text(encoding="utf-8"))
   93 |         return None
  134 |     return out
  138 |     return _read_json_silent(ROOT / "data" / "health_v12.json")
  142 |     return _read_json_silent(ROOT / "data" / "kpi_dashboard_v12.json")
  152 |             return rep
  153 |     return None
  233 |     return plan
  291 |     return "\n".join(lines)
  324 |     return out
  329 |     return 0
```

## `if` — 18 совпадений
```
   44 | if os.name == "nt" and not _USE_ANSI:
  101 |         if p.exists():
  102 |             if need == "OK":
  116 |             if need == "OK":
  151 |         if rep:
  167 |     if red_layout:
  173 |     if yellow_layout:
  179 |     if health is None:
  187 |         if verdict == "GREEN":
  199 |     if kpi is None:
  206 |         if verdict == "GREEN" and pct >= 95:
  218 |     if smoke is None:
  224 |         if failed == 0 and total > 0:
  231 |     if not plan:
  260 |         if smoke
  281 |         if it["severity"] == "green":
  313 |     if save_to_log:
  332 | if __name__ == "__main__":
```

## `for` — 10 совпадений
```
   99 |     for rel, need, descr in EXPECTED_PATHS:
  149 |     for name in ("smoke_v29_report.json", "smoke_v26_report.json", "smoke_v12_report.json"):
  169 |         for it in red_layout:
  175 |         for it in yellow_layout:
  191 |             for a in (adv or [])[:5]:
  195 |             for a in (adv or [])[:5]:
  210 |             for a in (kpi.get("advice", []) or [])[:3]:
  214 |             for a in (kpi.get("advice", []) or [])[:3]:
  273 |     for line in plan:
  280 |     for it in layout:
```

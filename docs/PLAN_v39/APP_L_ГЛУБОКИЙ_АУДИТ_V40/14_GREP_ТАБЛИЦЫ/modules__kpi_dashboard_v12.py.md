# grep-таблицы `modules/kpi_dashboard_v12.py`

## `import` — 6 совпадений
```
   18 | from __future__ import annotations
   20 | import json
   21 | import time
   22 | from dataclasses import asdict, dataclass, field
   23 | from pathlib import Path
   24 | from typing import Any
```

## `print` — 1 совпадений
```
  406 |     print(render_text(dash))
```

## `except` — 2 совпадений
```
   89 |     except Exception:
  346 |         except Exception:
```

## `try` — 2 совпадений
```
   87 |     try:
  335 |         try:
```

## `def` — 12 совпадений
```
   82 |     def as_dict(self) -> dict[str, Any]:
   86 | def _load_json(p: Path) -> dict[str, Any] | None:
   93 | def _newest(pattern: str, base: Path) -> Path | None:
  100 | def _health_section(health: dict[str, Any] | None) -> DashboardSection:
  126 | def _pipeline_section(pipe: dict[str, Any] | None) -> DashboardSection:
  155 | def _smoke_section(smoke: dict[str, Any] | None) -> DashboardSection:
  177 | def _tz_percent(
  208 |     def has(p: str) -> bool:
  297 | def build(save: bool = True) -> Dashboard:
  351 | def render_markdown(dash: Dashboard) -> str:
  380 | def render_text(dash: Dashboard) -> str:
  404 | def main() -> int:
```

## `class` — 2 совпадений
```
   66 | class DashboardSection:
   74 | class Dashboard:
```

## `raise` — 1 совпадений
```
  411 |     raise SystemExit(main())
```

## `return` — 17 совпадений
```
   83 |         return asdict(self)
   88 |         return json.loads(p.read_text(encoding="utf-8"))
   90 |         return None
   96 |         return None
   97 |     return max(matches, key=lambda p: p.stat().st_mtime)
  102 |         return DashboardSection(
  123 |     return DashboardSection("Стек / зависимости", v == "GREEN", percent, lines)
  128 |         return DashboardSection(
  150 |     return DashboardSection(
  157 |         return DashboardSection(
  174 |     return DashboardSection(f"Smoke-тесты ({label})", failed == 0, pct, lines)
  209 |         return (ROOT / p).exists()
  294 |     return percent, entries, advice
  348 |     return dash
  377 |     return "\n".join(lines) + "\n"
  401 |     return "\n".join(out)
  407 |     return 0 if dash.verdict == "GREEN" else (1 if dash.verdict == "YELLOW" else 2)
```

## `if` — 16 совпадений
```
   95 |     if not matches:
  101 |     if not health:
  127 |     if not pipe:
  156 |     if not smoke:
  263 |     if health is not None:
  266 |         if not int_ok.get("modules.rvc_manager", True) or not int_ok.get(
  270 |         if not int_ok.get("app.core.musicgen_texture", True):
  272 |         if not int_ok.get("modules.hit_kpi_monitor_v11", True):
  282 |         if ok:
  289 |         if not e["ok"]:
  310 |         if smoke:
  327 |     if s1.ok and s2.ok and s3.ok and tz_pct >= 90:
  334 |     if save:
  373 |     if dash.advice:
  395 |     if dash.advice:
  410 | if __name__ == "__main__":
```

## `for` — 15 совпадений
```
  121 |     for a in (health.get("advice") or [])[:8]:
  142 |     for s in pipe.get("stages", [])[:20]:
  170 |     for name, ok in list(smoke.get("cases", {}).items())[:30]:
  214 |             for m in [
  277 |     for item in TZ_CHECKLIST:
  288 |     for e in entries:
  304 |     for cand in (
  361 |     for s in dash.sections:
  364 |         for ln in s.get("lines", []):
  369 |     for i, c in enumerate(dash.checklist, 1):
  375 |         for a in dash.advice:
  387 |     for s in dash.sections:
  389 |         for ln in s.get("lines", []):
  393 |     for c in dash.checklist:
  398 |         for a in dash.advice[:15]:
```

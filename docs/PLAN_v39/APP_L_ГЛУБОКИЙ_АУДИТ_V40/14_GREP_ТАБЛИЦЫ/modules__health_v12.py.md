# grep-таблицы `modules/health_v12.py`

## `import` — 11 совпадений
```
   24 | from __future__ import annotations
   26 | import importlib
   27 | import json
   28 | import platform
   29 | import sys
   30 | import time
   31 | import traceback
   32 | from dataclasses import asdict, dataclass, field
   33 | from pathlib import Path
   34 | from typing import Any
  164 |         from app.core import hw_autodetect  # type: ignore
```

## `print` — 21 совпадений
```
  334 |     print("=" * 72)
  335 |     print("ZS Music Maker v12 — Health Check")
  336 |     print(f"Generated: {rep.generated_at_human}")
  337 |     print(f"Platform : {rep.platform}   Python: {rep.python}")
  338 |     print(
  342 |     print("-" * 72)
  343 |     print("EXTERNAL DEPENDENCIES:")
  345 |         print(_fmt_row(e["name"], e["ok"], e.get("version"), e["requirement"]))
  346 |     print("-" * 72)
  347 |     print("INTERNAL MODULES:")
  349 |         print(_fmt_row(e["name"], e["ok"], None, e["requirement"]))
  350 |     print("-" * 72)
  351 |     print(
  366 |             print(f"  ! RED причина: отсутствует ЯДРО: {', '.join(core_missing)}")
  368 |             print(f"  ! RED причина: нет GUI-бэкенда ({', '.join(gui_missing)}).")
  369 |             print("    Аудио-ядро (beat/mix/mastering) при этом может быть полностью")
  370 |             print("    рабочим — проверь `python tools/smoke_v29.py`. Установи GUI:")
  371 |             print("    `pip install PySide6` или `pip install gradio`.")
  373 |         print("ADVICE:")
  375 |             print(f"  - {a}")
  376 |     print("=" * 72)
```

## `except` — 3 совпадений
```
  157 |     except Exception as e:  # noqa: BLE001
  172 |     except Exception as e:  # noqa: BLE001
  314 |     except Exception:  # noqa: BLE001
```

## `try` — 3 совпадений
```
  150 |     try:
  163 |     try:
  309 |     try:
```

## `def` — 8 совпадений
```
  119 |     def as_dict(self) -> dict[str, Any]:
  140 |     def as_dict(self) -> dict[str, Any]:
  149 | def _probe(mod_path: str, name: str, req: str) -> ProbeResult:
  161 | def _hw_probe() -> dict[str, Any]:
  192 | def _advice_for(probe: ProbeResult) -> str | None:
  221 | def collect(save_to: Path | None = None) -> HealthReport:
  325 | def _fmt_row(name: str, ok: bool, ver: str | None, req: str) -> str:
  331 | def main(argv: list[str] | None = None) -> int:
```

## `class` — 2 совпадений
```
  111 | class ProbeResult:
  124 | class HealthReport:
```

## `raise` — 1 совпадений
```
  381 |     raise SystemExit(main())
```

## `return` — 10 совпадений
```
  120 |         return asdict(self)
  141 |         return asdict(self)
  156 |         return ProbeResult(mod_path, name, req, True, str(ver) if ver else None)
  158 |         return ProbeResult(mod_path, name, req, False, None, f"{type(e).__name__}: {e}")
  184 |     return profile
  195 |         return None
  218 |     return hint.get(probe.key)
  317 |     return rep
  328 |     return f"  [{mark}] [{req:<8}] {name} {v}"
  377 |     return 0 if rep.core_ok else 2
```

## `if` — 17 совпадений
```
  153 |         if ver is None and hasattr(m, "version"):
  167 |             if hasattr(hw_autodetect, m):
  169 |                 if isinstance(p, dict):
  176 |     if not profile:
  194 |     if probe.ok:
  236 |         if entry.get("group") == "gui" and r.ok:
  284 |     if not rep.core_ok:
  293 |         if not e["ok"]:
  299 |             if adv:
  302 |         if not e["ok"]:
  307 |     if save_to is None:
  360 |     if rep.verdict == "RED":
  362 |                         if e["requirement"] == "core" and not e["ok"]]
  364 |                        if e.get("requirement") == "core_alt" and not e["ok"]]
  365 |         if core_missing:
  372 |     if rep.advice:
  380 | if __name__ == "__main__":
```

## `for` — 8 совпадений
```
  166 |         for m in ("detect_hardware", "detect", "probe"):
  233 |     for entry in CHECKS:
  240 |     for mp in INTERNAL_MODULES:
  292 |     for e in rep.externals:
  301 |     for e in rep.internals:
  344 |     for e in rep.externals:
  348 |     for e in rep.internals:
  374 |         for a in rep.advice[:20]:
```

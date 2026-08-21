# grep-таблицы `modules/wizard_v12_integration.py`

## `import` — 13 совпадений
```
   21 | from __future__ import annotations
   23 | import json
   24 | import sys
   25 | import time
   26 | from collections.abc import Callable
   27 | from dataclasses import asdict, dataclass, field
   28 | from pathlib import Path
   29 | from typing import Any
  133 |         from modules import health_v12
  153 |         from app.core import orchestrator_v12_patch as orch
  169 |             from app.core import orchestrator_v11_patch as v11
  187 |                 from modules import master_pipeline_v12 as mp
  202 |         from modules import kpi_dashboard_v12 as kd
```

## `print` — 3 совпадений
```
   42 |         print(line)
  281 |     print(
  284 |     print(r.human_summary)
```

## `except` — 9 совпадений
```
   43 |     except UnicodeEncodeError:
   47 |     except Exception:
  143 |             except Exception:
  145 |     except Exception as e:  # noqa: BLE001
  162 |     except Exception as e:  # noqa: BLE001
  183 |         except Exception as e:  # noqa: BLE001
  197 |             except Exception as e2:  # noqa: BLE001
  210 |     except Exception as e:  # noqa: BLE001
  269 |     except Exception as e:  # noqa: BLE001
```

## `try` — 9 совпадений
```
   41 |     try:
   45 |     try:
  132 |     try:
  139 |             try:
  150 |     try:
  168 |         try:
  186 |             try:
  201 |     try:
  243 |     try:
```

## `def` — 7 совпадений
```
   39 | def _log(msg: str) -> None:
   64 |     def as_dict(self) -> dict[str, Any]:
   70 | def collect_wizard_state(ui_state: dict[str, Any] | None = None) -> dict[str, Any]:
   94 | def bridge_wizard_to_v12(
  234 | def install_into_wizard_main(main_module: Any) -> bool:
  249 |         def patched(*args, **kwargs):
  274 | def main_entry() -> int:
```

## `class` — 1 совпадений
```
   52 | class WizardBridgeResult:
```

## `raise` — 2 совпадений
```
  152 |             raise RuntimeError("forced v11 path")
  289 |     raise SystemExit(main_entry())
```

## `return` — 8 совпадений
```
   67 |         return d
   91 |     return state
  231 |     return res
  245 |             return False
  254 |             return bridge_wizard_to_v12(
  268 |         return True
  271 |         return False
  285 |     return 0 if r.verdict.endswith("PASS") else 1
```

## `if` — 8 совпадений
```
   32 | if str(ROOT) not in sys.path:
  138 |         if progress_cb:
  151 |         if force_v11:
  167 |     if not str(res.verdict).endswith("PASS"):
  171 |             if hasattr(v11, "run_full_pipeline_v11"):
  178 |                 if isinstance(v11_out, dict) and str(
  244 |         if not hasattr(main_module, "run_pipeline"):
  288 | if __name__ == "__main__":
```

## `open` — 1 совпадений
```
   46 |         (LOGS / "app.log").open("a", encoding="utf-8").write(line + "\n")
```

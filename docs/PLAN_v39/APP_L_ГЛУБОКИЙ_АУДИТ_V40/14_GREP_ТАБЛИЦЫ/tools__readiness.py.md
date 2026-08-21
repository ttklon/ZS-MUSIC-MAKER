# grep-таблицы `tools/readiness.py`

## `import` — 7 совпадений
```
    7 | from __future__ import annotations
    9 | import json
   10 | import math
   11 | import sys
   12 | from pathlib import Path
   13 | from typing import Any
  165 |         from modules import voice_recording as vr
```

## `print` — 1 совпадений
```
  278 |     print(json.dumps({"percent": pct, "blocks": blocks}, ensure_ascii=False, indent=2))
```

## `except` — 9 совпадений
```
   50 |     except Exception:
  116 |     except Exception:
  120 |     except Exception:
  124 |     except Exception:
  128 |     except Exception:
  132 |     except Exception:
  136 |     except Exception:
  171 |     except Exception:
  187 |     except Exception:
```

## `try` — 9 совпадений
```
   47 |     try:
  114 |     try:
  118 |     try:
  122 |     try:
  126 |     try:
  130 |     try:
  134 |     try:
  164 |     try:
  185 |     try:
```

## `def` — 12 совпадений
```
   46 | def _module_exists(name: str) -> bool:
   54 | def _file_exists(rel: str) -> bool:
   58 | def probe_architecture() -> dict[str, str]:
   81 | def probe_core_modules() -> dict[str, str]:
  112 | def probe_audio_pipeline() -> dict[str, str]:
  151 | def probe_voice_rvc() -> dict[str, str]:
  176 | def probe_release() -> dict[str, str]:
  192 | def probe_installer() -> dict[str, str]:
  203 | def probe_testing() -> dict[str, str]:
  218 | def _block_percent(probes: dict[str, str]) -> float:
  226 | def compute() -> tuple[float, dict[str, Any]]:
  276 | def main() -> int:
```

## `raise` — 1 совпадений
```
  283 |     raise SystemExit(main())
```

## `return` — 14 совпадений
```
   49 |         return True
   51 |         return False
   55 |     return (ROOT / rel).exists()
   78 |     return p
  109 |     return p
  148 |     return p
  173 |     return p
  189 |     return p
  200 |     return p
  215 |     return p
  220 |         return 0.0
  223 |     return round(100.0 * score / n, 2)
  265 |     return float(final), {
  279 |     return 0
```

## `if` — 12 совпадений
```
   21 | if str(ROOT) not in sys.path:
   63 |         if _file_exists("main.py") and not stray
  139 |     if _file_exists("output/audit_v14/e2e_summary.json") or _file_exists(
  219 |     if not probes:
  243 |     if blocks_raw["voice_rvc"].get("rvc_model") != "REAL_PASS":
  245 |     if blocks_raw["voice_rvc"].get("mic_recording") != "REAL_PASS":
  247 |     if blocks_raw["audio_pipeline"].get("e2e_run_evidence") != "REAL_PASS":
  249 |     if blocks_raw["installer"].get("updater_module") != "REAL_PASS":
  254 |         if blocks_raw["audio_pipeline"].get(k) in ("MOCK", "FAILED", "MISSING")
  256 |     if heavy_missing:
  258 |     if blocks_raw["testing"].get("evidence_present") not in ("REAL_PASS", "PARTIAL"):
  282 | if __name__ == "__main__":
```

## `for` — 2 совпадений
```
  239 |     for k, w in WEIGHTS.items():
  253 |         for k in ("musicgen", "demucs")
```

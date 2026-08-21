# grep-таблицы `modules/arrangement_engine.py`

## `import` — 5 совпадений
```
   23 | from __future__ import annotations
   25 | import json
   26 | import random
   27 | import time
   28 | from pathlib import Path
```

## `print` — 1 совпадений
```
  325 |     print(json.dumps(p, ensure_ascii=False, indent=2)[:3000])
```

## `def` — 6 совпадений
```
  120 | def _pick(rng, patterns_dict, keys):
  128 | def _bars_to_seconds(bars: int, bpm: float, beats_per_bar: int = 4) -> float:
  132 | def _clamp(x, lo, hi):
  137 | def build_arrangement(
  292 | def _guess_genre(sv: dict) -> str:
  307 | def save_plan(plan: dict, out_path: str) -> str:
```

## `return` — 12 совпадений
```
  123 |             return k, patterns_dict[k]
  125 |     return k, patterns_dict[k]
  129 |     return bars * beats_per_bar * (60.0 / max(bpm, 1e-3))
  133 |     return max(lo, min(hi, x))
  289 |     return plan
  295 |         return "phonk / drift"
  297 |         return "dance / edm"
  299 |         return "trap / hip-hop"
  301 |         return "pop / r&b"
  303 |         return "hardstyle / techno"
  304 |     return "generic hit"
  312 |     return out_path
```

## `if` — 13 совпадений
```
  122 |         if k in patterns_dict:
  166 |     if "phonk" in genre:
  194 |         if variant >= 1 and "chorus" in name:
  196 |         if variant >= 2 and name in ("verse1", "verse2"):
  209 |         if name.startswith(("chorus", "drop")) and (prev_name or "").startswith(
  214 |         if name.startswith(("outro", "break")):
  253 |     if hot_sections:
  294 |     if 130 <= bpm <= 145:
  296 |     if 120 <= bpm < 130:
  298 |     if 70 <= bpm <= 100:
  300 |     if 95 <= bpm < 120:
  302 |     if bpm > 150:
  316 | if __name__ == "__main__":
```

## `for` — 2 совпадений
```
  121 |     for k in keys:
  189 |     for i, (name, bars_def, energy, vrole) in enumerate(template):
```

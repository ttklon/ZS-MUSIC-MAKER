# grep-таблицы `modules/reference_ingest.py`

## `import` — 8 совпадений
```
   22 | from __future__ import annotations
   24 | import hashlib
   25 | import json
   26 | import time
   27 | from pathlib import Path
   30 |     import numpy as np
   35 |     import librosa
  312 |     import sys
```

## `print` — 2 совпадений
```
  315 |         print("usage: python reference_ingest.py <ref1> [ref2 ...]")
  318 |     print(json.dumps(r, ensure_ascii=False, indent=2))
```

## `except` — 4 совпадений
```
   31 | except Exception:  # pragma: no cover
   38 | except Exception:
   67 |         except Exception:
  164 |     except Exception as e:
```

## `try` — 4 совпадений
```
   29 | try:
   34 | try:
   65 |         try:
  125 |     try:
```

## `def` — 13 совпадений
```
   50 | def _md5(path: str) -> str:
   58 | def _cache_path(path: str) -> Path:
   62 | def _load_cached(path: str) -> dict | None:
   72 | def _save_cached(path: str, data: dict) -> None:
   77 | def _key_from_chroma(chroma) -> tuple[str, str]:
  100 | def analyze_file(path: str, sr: int = 22050, use_cache: bool = True) -> dict:
  169 | def _consensus_bpm(features: list[dict], weights: list[float]) -> float:
  175 |     def _norm(b):
  188 | def _consensus_key(features: list[dict], weights: list[float]) -> tuple[str, str]:
  201 | def build_style_vector(
  232 |     def _wavg(field, dim=None):
  281 | def _guess_genre(sv: dict) -> str:
  298 | def _guess_mood(sv: dict) -> str:
```

## `return` — 33 совпадений
```
   55 |     return h.hexdigest()
   59 |     return CACHE_DIR / f"{_md5(path)}.json"
   66 |             return json.loads(cp.read_text(encoding="utf-8"))
   68 |             return None
   69 |     return None
   80 |         return "C", "major"
   97 |     return best[0], best[1]
  104 |         return {"ok": False, "error": f"not found: {path}"}
  109 |             return cached
  123 |         return result
  163 |         return result
  165 |         return {"ok": False, "error": str(e), "path": str(p)}
  172 |         return 130.0
  180 |         return b
  185 |     return round(weighted, 2)
  196 |         return "C", "minor"
  198 |     return best
  209 |         return {"ok": False, "error": "no references given"}
  226 |         return {"ok": False, "error": "all analyses failed", "per_file": per_file}
  235 |             return None
  244 |             return [round(x / tw, 4) for x in out]
  245 |         return round(sum(v * w for v, w in zip(vals, ws)) / tw, 4)
  264 |     return {
  286 |         return "phonk / drift"
  288 |         return "dance / edm"
  290 |         return "trap / hip-hop"
  292 |         return "pop / r&b"
  294 |         return "hardstyle / techno"
  295 |     return "generic hit"
  302 |         return "dark / moody"
  304 |         return "energetic / driving"
  306 |         return "bright / summer"
  307 |     return "melancholic"
```

## `if` — 30 совпадений
```
   64 |     if cp.exists():
   79 |     if np is None:
   93 |         if s_maj > best[2]:
   95 |         if s_min > best[2]:
  103 |     if not p.exists():
  106 |     if use_cache:
  108 |         if cached is not None:
  111 |     if not HAS_LIBROSA:
  121 |         if use_cache:
  161 |         if use_cache:
  171 |     if not features:
  195 |     if not tally:
  208 |     if not files:
  210 |     if len(files) > 7:
  212 |     if weights is None:
  214 |     if len(weights) != len(files):
  222 |         if r.get("ok"):
  225 |     if not features:
  234 |         if not vals:
  238 |         if isinstance(vals[0], list):
  285 |     if 130 <= bpm <= 145 and od > 3.5:
  287 |     if 120 <= bpm <= 132 and hr > 0.5:
  289 |     if 70 <= bpm <= 100 and od < 3.0:
  291 |     if 95 <= bpm <= 120:
  293 |     if bpm > 150:
  301 |     if mode == "minor" and centroid < 1800:
  303 |     if mode == "minor" and centroid >= 1800:
  305 |     if mode == "major" and centroid > 2200:
  311 | if __name__ == "__main__":
  314 |     if len(sys.argv) < 2:
```

## `for` — 6 совпадений
```
   53 |         for chunk in iter(lambda: f.read(1 << 16), b""):
   89 |     for i in range(12):
  191 |     for f, w in zip(features, weights):
  219 |     for path, w in zip(files, weights):
  241 |             for v, w in zip(vals, ws):
  242 |                 for i in range(L):
```

## `while` — 2 совпадений
```
  176 |         while b < 60:
  178 |         while b > 200:
```

## `with` — 1 совпадений
```
   52 |     with open(path, "rb") as f:
```

## `open` — 1 совпадений
```
   52 |     with open(path, "rb") as f:
```

## `np` — 5 совпадений
```
   81 |     major_prof = np.array(
   84 |     minor_prof = np.array(
   90 |         rot = np.roll(chroma_mean, -i)
   91 |         s_maj = float(np.dot(rot, major_prof))
   92 |         s_min = float(np.dot(rot, minor_prof))
```

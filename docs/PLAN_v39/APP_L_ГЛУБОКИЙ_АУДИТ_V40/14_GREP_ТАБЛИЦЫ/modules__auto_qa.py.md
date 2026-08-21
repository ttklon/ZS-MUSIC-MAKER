# grep-таблицы `modules/auto_qa.py`

## `import` — 10 совпадений
```
   21 | from __future__ import annotations
   23 | import json
   24 | import math
   25 | import time
   26 | from pathlib import Path
   35 |     import numpy as np
   58 |         import librosa
   59 |         import numpy as np
  105 |         from modules.ai_detector_pro import analyze_track
  131 |         import soundfile as sf
```

## `except` — 3 совпадений
```
   83 |     except Exception as e:
  126 |     except Exception as e:
  166 |     except Exception as e:
```

## `try` — 3 совпадений
```
   57 |     try:
  104 |     try:
  130 |     try:
```

## `def` — 4 совпадений
```
   33 | def _loudness(y, sr) -> dict:
   55 | def _structure_check(y, sr) -> dict:
   87 | def audit_track(master_wav: str | Path, target_lufs: float = -9.0) -> dict:
  191 | def should_retry(
```

## `return` — 9 совпадений
```
   47 |     return {
   65 |             return {"hook_score": 0.0, "sections_detected": 0}
   79 |         return {
   84 |         return {"hook_score": 0.0, "error": str(e)}
  101 |         return result
  188 |     return result
  199 |         return False, []
  202 |         return False, []
  204 |     return True, targets
```

## `if` — 12 совпадений
```
   37 |     if y.ndim > 1:
   64 |         if len(rms) < 3 * w:
   72 |                 if len(a) != len(b):
   99 |     if not master_wav.exists():
  110 |         if neuro and neuro > 70:
  134 |         if y.ndim > 1:
  142 |         if lu < target_lufs - 3:
  150 |         if result["loudness"]["peak_db"] > -0.2:
  158 |         if result["structure"]["hook_score"] < 0.35:
  171 |     if n_actions == 0:
  198 |     if current_iter >= max_iterations:
  201 |     if verdict == "release":
```

## `for` — 2 совпадений
```
   68 |         for i in range(len(chunks)):
   69 |             for j in range(i + 2, len(chunks)):
```

## `np` — 4 совпадений
```
   41 |     peak = float(np.max(np.abs(m))) if len(m) else 0.0
   42 |     rms = float(np.sqrt(np.mean(m * m))) if len(m) else 0.0
   76 |                 den = np.linalg.norm(da) * np.linalg.norm(db) + 1e-9
   77 |                 c = float(np.dot(da, db) / den)
```

## `sf` — 1 совпадений
```
  133 |         y, sr = sf.read(str(master_wav))
```

# grep-таблицы `modules/ai_detector_pro.py`

## `import` — 6 совпадений
```
   12 | from __future__ import annotations
   14 | import os
   51 |         import librosa
   52 |         import numpy as np
  185 |     import sys
  188 |     import json
```

## `print` — 1 совпадений
```
  190 |     print(json.dumps(r, ensure_ascii=False, indent=2))
```

## `except` — 11 совпадений
```
   53 |     except ImportError:
   58 |     except Exception as e:
   71 |     except Exception:
   84 |     except Exception:
   94 |     except Exception:
  102 |     except Exception:
  109 |     except Exception:
  121 |     except Exception:
  134 |     except Exception:
  142 |     except Exception:
  151 |     except Exception:
```

## `try` — 11 совпадений
```
   50 |     try:
   56 |     try:
   65 |     try:
   75 |     try:
   88 |     try:
   98 |     try:
  106 |     try:
  113 |     try:
  125 |     try:
  138 |     try:
  146 |     try:
```

## `def` — 1 совпадений
```
   43 | def analyze_track(audio_path: str) -> dict:
```

## `return` — 4 совпадений
```
   48 |         return {"error": f"файл не найден: {audio_path}"}
   54 |         return {"error": "librosa/numpy не установлены"}
   59 |         return {"error": f"load failed: {e}"}
  173 |     return {
```

## `if` — 4 совпадений
```
   47 |     if not audio_path or not os.path.exists(audio_path):
  159 |         if v < lo or v > hi:
  164 |     if score > 0.85:
  184 | if __name__ == "__main__":
```

## `for` — 1 совпадений
```
  157 |     for m, (lo, hi) in THRESHOLDS.items():
```

## `np` — 20 совпадений
```
   67 |         rms_db = 20 * np.log10(rms + 1e-9)
   69 |             np.percentile(rms_db, 95) - np.percentile(rms_db, 5)
   76 |         env = rms - np.mean(rms)
   77 |         corr = np.correlate(env, env, mode="full")[len(env) - 1 :]
   82 |         peak = float(np.max(corr[lag_min:lag_max])) if len(corr) > lag_max else 0.0
   89 |         S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
   91 |         cols = S / (np.linalg.norm(S, axis=0, keepdims=True) + 1e-9)
   92 |         corrs = np.sum(cols[:, 1:] * cols[:, :-1], axis=0)
   93 |         metrics["spectral_stability"] = float(np.mean(corrs))
  100 |         eh, ep = float(np.mean(y_h**2)), float(np.mean(y_p**2))
  108 |         metrics["hi_flatness"] = float(np.mean(flat))
  119 |             1.0 - min(1.0, np.std(zcr) / (np.mean(zcr) + 1e-9))
  128 |         c = chroma - np.mean(chroma, axis=1, keepdims=True)
  129 |         c = c / (np.linalg.norm(c, axis=0, keepdims=True) + 1e-9)
  130 |         sim = np.dot(c.T, c)
  132 |         off = sim - np.diag(np.diag(sim))
  133 |         metrics["hook_repeatability"] = float(np.mean(np.abs(off)))
  139 |         rms_norm = rms / (np.max(rms) + 1e-9)
  141 |         metrics["volume_uniformity"] = float(1.0 - min(1.0, np.std(rms_norm) * 2))
  149 |         v = float(np.std(cent) / (np.mean(cent) + 1e-9))
```

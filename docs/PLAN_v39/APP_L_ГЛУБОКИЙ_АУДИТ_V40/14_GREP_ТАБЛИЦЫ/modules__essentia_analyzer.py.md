# grep-таблицы `modules/essentia_analyzer.py`

## `import` — 9 совпадений
```
   20 | from __future__ import annotations
   22 | import json
   23 | import logging
   24 | from pathlib import Path
   25 | from typing import Any
   30 |     import essentia.standard as es  # type: ignore
   38 |     import librosa
   39 |     import numpy as np
  166 |     import sys
```

## `print` — 2 совпадений
```
  169 |         print(json.dumps({"engine_available": ESSENTIA_OK}, ensure_ascii=False))
  172 |         print(json.dumps(rep, ensure_ascii=False, indent=2))
```

## `except` — 4 совпадений
```
   33 | except Exception:
   40 | except Exception:
   59 |         except Exception as e:
  155 |     except Exception as e:
```

## `try` — 4 совпадений
```
   29 | try:
   37 | try:
   57 |         try:
  119 |     try:
```

## `def` — 4 совпадений
```
   45 | def analyze_advanced(audio_path: str, sr: int = 44100) -> dict[str, Any]:
   65 | def _analyze_essentia(audio_path: str, sr: int) -> dict[str, Any]:
  116 | def _analyze_librosa_fallback(audio_path: str, sr: int) -> dict[str, Any]:
  159 | def save_report(report: dict[str, Any], out_json: str) -> None:
```

## `return` — 7 совпадений
```
   54 |         return {"ok": False, "reason": f"file not found: {audio_path}"}
   58 |             return _analyze_essentia(str(p), sr)
   62 |     return _analyze_librosa_fallback(str(p), sr)
   99 |     return {
  118 |         return {"ok": False, "reason": "no librosa & no essentia"}
  138 |         return {
  156 |         return {"ok": False, "reason": str(e)}
```

## `if` — 7 совпадений
```
   53 |     if not p.exists():
   56 |     if ESSENTIA_OK:
  117 |     if librosa is None:
  133 |         if len(beats) > 2:
  145 |                 if np.mean(chroma[[0, 4, 7]]) > np.mean(chroma[[0, 3, 7]])
  165 | if __name__ == "__main__":
  168 |     if len(sys.argv) < 2:
```

## `for` — 1 совпадений
```
   91 |                 for fr in es.FrameGenerator(audio, 2048, 1024)
```

## `with` — 1 совпадений
```
  161 |     with open(out_json, "w", encoding="utf-8") as f:
```

## `open` — 1 совпадений
```
  161 |     with open(out_json, "w", encoding="utf-8") as f:
```

## `np` — 9 совпадений
```
   88 |         np.mean(
  123 |         onset_rate = float(np.mean(onset_env))
  124 |         rms = float(np.mean(librosa.feature.rms(y=y)))
  125 |         centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
  126 |         flatness = float(np.mean(librosa.feature.spectral_flatness(y=y)))
  128 |         key_idx = int(np.argmax(np.mean(chroma, axis=1)))
  134 |             intervals = np.diff(librosa.frames_to_time(beats, sr=sr))
  135 |             beat_stability = 1.0 / (1.0 + float(np.std(intervals)))
  145 |                 if np.mean(chroma[[0, 4, 7]]) > np.mean(chroma[[0, 3, 7]])
```

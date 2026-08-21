# grep-таблицы `modules/analyzer.py`

## `import` — 6 совпадений
```
   11 | import json
   12 | import os
   14 | import numpy as np
   17 |     import librosa
   80 |         import essentia.standard as estd
  250 |     import sys
```

## `print` — 2 совпадений
```
  254 |         print("Usage: python analyzer.py <ref1.mp3> [ref2.mp3 ...]")
  257 |         print(json.dumps(result, ensure_ascii=False, indent=2))
```

## `except` — 4 совпадений
```
   18 | except ImportError:
   86 |     except Exception:
  232 |         except Exception:
  244 |         except Exception:
```

## `try` — 4 совпадений
```
   16 | try:
   79 |     try:
  230 |         try:
  242 |         try:
```

## `def` — 7 совпадений
```
   26 | def _safe_load(path, sr=22050):
   33 | def analyze_single(path: str) -> dict:
  110 | def _infer_vibe(bpm, centroid, bass, mode):
  135 | def _bpm_range(bpm_val: float) -> dict:
  158 | def analyze_multi(paths: list, weights: list = None, take_notes: list = None) -> dict:
  226 | def _save_to_vault(data):
  240 | def list_cached_analyses() -> list:
```

## `raise` — 1 совпадений
```
   28 |         raise RuntimeError("librosa не установлен. pip install librosa")
```

## `return` — 8 совпадений
```
   30 |     return y, sr
   89 |     return {
  132 |     return tags
  139 |     return {
  223 |     return style_vector
  243 |             return json.load(open(VAULT, "r", encoding="utf-8"))
  245 |             return []
  246 |     return []
```

## `if` — 14 совпадений
```
   27 |     if librosa is None:
  112 |     if bpm < 90:
  122 |     if bass > 1.4:
  124 |     if centroid < 1500:
  128 |     if mode == "minor":
  130 |     if bass > 2.0 and centroid < 2000:
  169 |     if weights is None:
  182 |         if sum(1 for k in keys_list if "minor" in k) >= len(keys_list) / 2
  198 |     if take_notes:
  200 |             if i < len(analyses) and note.strip():
  229 |     if os.path.exists(VAULT):
  241 |     if os.path.exists(VAULT):
  249 | if __name__ == "__main__":
  253 |     if not files:
```

## `for` — 4 совпадений
```
   72 |         for i in range(n_sections)
  188 |     for a, w in zip(analyses, weights):
  189 |         for t in a["vibe_tags"]:
  199 |         for i, note in enumerate(take_notes):
```

## `open` — 3 совпадений
```
  231 |             existing = json.load(open(VAULT, "r", encoding="utf-8"))
  236 |         existing, open(VAULT, "w", encoding="utf-8"), ensure_ascii=False, indent=2
  243 |             return json.load(open(VAULT, "r", encoding="utf-8"))
```

## `np` — 9 совпадений
```
   39 |     bpm_val = float(tempo) if np.ndim(tempo) == 0 else float(tempo[0])
   43 |     key_idx = int(np.argmax(chroma.mean(axis=1)))
   51 |     rms = float(np.mean(librosa.feature.rms(y=y)))
   52 |     centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
   53 |     bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)))
   54 |     zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)))
   58 |     S = np.abs(librosa.stft(y))
   71 |         float(np.mean(rms_frames[i * chunk : (i + 1) * chunk]))
   75 |     drop_section = int(np.argmax(section_energies)) if section_energies else 0
```

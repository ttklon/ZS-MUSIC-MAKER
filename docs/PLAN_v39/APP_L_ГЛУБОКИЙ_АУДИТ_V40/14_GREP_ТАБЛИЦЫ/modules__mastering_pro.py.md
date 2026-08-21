# grep-таблицы `modules/mastering_pro.py`

## `import` — 8 совпадений
```
   18 | import os
   19 | import numpy as np
   20 | import soundfile as sf
   24 |     import pyloudnorm as pyln
   30 |     from pedalboard import (
   38 |     from pedalboard.io import AudioFile
   79 |             from pydub import AudioSegment
  131 |             import warnings
```

## `print` — 3 совпадений
```
   88 |             print(f"[mastering_pro] Mix failed: {e}")
  112 |             print(f"[mastering_pro] Pedalboard execution error: {e}, falling back to numpy/soundfile")
  137 |             print(f"[mastering_pro] pyloudnorm error: {e}, using RMS fallback")
```

## `except` — 6 совпадений
```
   26 | except ImportError:
   40 | except ImportError:
   87 |         except Exception as e:
  111 |         except Exception as e:
  136 |         except Exception as e:
  175 |         except Exception:
```

## `try` — 6 совпадений
```
   23 | try:
   29 | try:
   78 |         try:
   96 |         try:
  127 |         try:
  172 |         try:
```

## `def` — 3 совпадений
```
   44 | def _sanitize(x: np.ndarray) -> np.ndarray:
   51 | def _apply_ceiling(x: np.ndarray, ceiling_db: float = -1.0) -> np.ndarray:
   65 | def process_mastering(input_wav: str, output_wav: str, vocal_path: str = None, target_lufs: float = -14.0):
```

## `raise` — 1 совпадений
```
   74 |         raise FileNotFoundError(f"Input wav not found: {input_wav}")
```

## `return` — 3 совпадений
```
   48 |     return x
   62 |     return x
  178 |     return {
```

## `if` — 11 совпадений
```
   46 |     if not np.isfinite(x).all():
   60 |     if peak > ceiling and peak > 0:
   73 |     if not os.path.exists(input_wav):
   77 |     if vocal_path and os.path.exists(vocal_path):
   95 |     if HAS_PEDALBOARD:
  115 |     if not HAS_PEDALBOARD:
  126 |     if HAS_PYLOUDNORM:
  140 |     if not HAS_PYLOUDNORM:
  156 |     if mastered.ndim == 2 and mastered.shape[0] < mastered.shape[1]:
  160 |     if mastered.ndim == 1:
  171 |     if HAS_PYLOUDNORM:
```

## `with` — 2 совпадений
```
   97 |             with AudioFile(input_wav) as f:
  132 |             with warnings.catch_warnings():
```

## `np` — 12 совпадений
```
   44 | def _sanitize(x: np.ndarray) -> np.ndarray:
   46 |     if not np.isfinite(x).all():
   47 |         x = np.nan_to_num(x, nan=0.0, posinf=0.99, neginf=-0.99)
   51 | def _apply_ceiling(x: np.ndarray, ceiling_db: float = -1.0) -> np.ndarray:
   59 |     peak = float(np.max(np.abs(x))) if x.size else 0.0
  122 |     audio_to_norm = _sanitize(np.asarray(audio_to_norm))
  142 |         current_rms = np.sqrt(np.mean(mastered ** 2)) + 1e-12
  147 |     mastered = _sanitize(np.asarray(mastered))
  153 |     mastered = np.clip(mastered, -0.99, 0.99)
  161 |         mastered = np.stack([mastered, mastered], axis=1)
  163 |         mastered = np.concatenate([mastered, mastered], axis=1)
  169 |     output_peak_db = 20.0 * np.log10(float(np.max(np.abs(mastered))) + 1e-12)
```

## `sf` — 4 совпадений
```
   15 |     получить (frames,1) и sf.write писал моно WAV, сбивая God Mode).
  116 |         audio_data, samplerate = sf.read(input_wav, always_2d=True)
  155 |     # Приведение к (frames, channels) для sf.write
  166 |     sf.write(output_wav, mastered, samplerate, format="WAV", subtype="PCM_16")
```

# grep-таблицы `modules/pro_audio_dsp.py`

## `import` — 5 совпадений
```
    8 | import logging
    9 | import os
   10 | from typing import Dict, Any
   11 | import numpy as np
   12 | import soundfile as sf
```

## `def` — 2 совпадений
```
   22 |     def align_stereo_phases(audio: np.ndarray) -> np.ndarray:
   44 |     def apply_mastering_chain(
```

## `class` — 1 совпадений
```
   18 | class ProAudioDSP:
```

## `raise` — 1 совпадений
```
   52 |             raise FileNotFoundError(f"Input audio not found at {input_path}")
```

## `return` — 3 совпадений
```
   28 |             return audio
   41 |         return np.stack([left, right], axis=1)
   79 |         return {
```

## `if` — 4 совпадений
```
   27 |         if audio.ndim != 2 or audio.shape[1] < 2:
   36 |         if lag > 0:
   51 |         if not os.path.exists(input_path):
   72 |         if max_val > 0.99:
```

## `np` — 11 совпадений
```
   22 |     def align_stereo_phases(audio: np.ndarray) -> np.ndarray:
   33 |         corr = np.correlate(left, right, mode="full")
   34 |         lag = int(np.argmax(corr) - (len(right) - 1))
   37 |             right = np.pad(right[lag:], (0, lag), mode="constant")
   39 |             left = np.pad(left[-lag:], (0, -lag), mode="constant")
   41 |         return np.stack([left, right], axis=1)
   57 |         data = data - np.mean(data, axis=0)
   61 |         saturated = np.tanh(driven) * headroom
   63 |         current_rms = float(np.sqrt(np.mean(saturated**2)) + 1e-12)
   71 |         max_val = np.max(np.abs(normalized))
   75 |         final_audio = np.clip(normalized, -0.999, 0.999)
```

## `sf` — 2 совпадений
```
   54 |         data, sr = sf.read(input_path, always_2d=True)
   77 |         sf.write(output_path, final_audio, sr, format="WAV", subtype="PCM_16")
```

# grep-таблицы `modules/chanson_engine.py`

## `import` — 5 совпадений
```
   11 | import os
   12 | from typing import Dict, Any
   13 | import numpy as np
   14 | import soundfile as sf
   17 |     from pedalboard import (
```

## `except` — 3 совпадений
```
   26 | except ImportError:
   95 |             except Exception:
  182 |             except Exception:
```

## `try` — 3 совпадений
```
   16 | try:
   89 |             try:
  175 |             try:
```

## `def` — 6 совпадений
```
   33 |     def __init__(self, sample_rate: int = 44100) -> None:
   36 |     def generate_kick(self) -> np.ndarray:
   45 |     def generate_snare(self) -> np.ndarray:
   55 |     def generate_hihat(self, open_hat: bool = False) -> np.ndarray:
   66 |     def generate_guitar_chord(self, root_freqs: list, duration: float) -> np.ndarray:
  100 |     def synthesize_chanson_track(
```

## `class` — 1 совпадений
```
   30 | class ChansonEngine:
```

## `return` — 5 совпадений
```
   43 |         return np.clip(audio, -1.0, 1.0)
   53 |         return np.clip(audio, -1.0, 1.0)
   64 |         return np.clip(audio * 0.5, -1.0, 1.0)
   98 |         return np.clip(chord_signal, -0.99, 0.99)
  189 |         return {
```

## `if` — 10 совпадений
```
   75 |             if delay_samples >= n:
   88 |         if HAS_PEDALBOARD:
  140 |                 if beat_start + length <= total_samples:
  149 |                 if step in (0, 4):
  151 |                     if step_start + k_len <= total_samples:
  156 |                 if step in (2, 6):
  158 |                     if step_start + s_len <= total_samples:
  164 |                 if step_start + h_len <= total_samples:
  170 |             if current_sample >= total_samples:
  174 |         if HAS_PEDALBOARD:
```

## `for` — 3 совпадений
```
   72 |         for i, freq in enumerate(root_freqs):
  136 |             for beat in range(4):
  145 |             for step in range(8):
```

## `while` — 1 совпадений
```
  131 |         while current_sample < total_samples:
```

## `np` — 26 совпадений
```
   36 |     def generate_kick(self) -> np.ndarray:
   40 |         t = np.linspace(0, dur, n, endpoint=False)
   41 |         freq = 120.0 * np.exp(-t * 25.0) + 45.0
   42 |         audio = np.sin(2.0 * np.pi * freq * t) * np.exp(-t * 12.0)
   43 |         return np.clip(audio, -1.0, 1.0)
   45 |     def generate_snare(self) -> np.ndarray:
   49 |         t = np.linspace(0, dur, n, endpoint=False)
   50 |         body = np.sin(2.0 * np.pi * 180.0 * t) * np.exp(-t * 20.0)
   51 |         noise = np.random.uniform(-1.0, 1.0, n) * np.exp(-t * 15.0)
   53 |         return np.clip(audio, -1.0, 1.0)
   55 |     def generate_hihat(self, open_hat: bool = False) -> np.ndarray:
   59 |         t = np.linspace(0, dur, n, endpoint=False)
   60 |         noise = np.random.uniform(-1.0, 1.0, n)
   62 |         carrier = np.sin(2.0 * np.pi * 8000.0 * t)
   63 |         audio = noise * carrier * np.exp(-t * (30.0 if not open_hat else 10.0))
   64 |         return np.clip(audio * 0.5, -1.0, 1.0)
   66 |     def generate_guitar_chord(self, root_freqs: list, duration: float) -> np.ndarray:
   69 |         t = np.linspace(0, duration, n, endpoint=False)
   70 |         chord_signal = np.zeros(n, dtype=np.float32)
   80 |                 np.sin(2.0 * np.pi * freq * sub_t) +
   81 |                 0.5 * np.sin(2.0 * np.pi * freq * 2.0 * sub_t) +
   82 |                 0.25 * np.sin(2.0 * np.pi * freq * 3.0 * sub_t)
   84 |             env = np.exp(-sub_t * 3.5)
   98 |         return np.clip(chord_signal, -0.99, 0.99)
  108 |         stereo_mix = np.zeros((total_samples, 2), dtype=np.float32)
  185 |         stereo_mix = np.clip(stereo_mix, -0.99, 0.99)
```

## `sf` — 1 совпадений
```
  187 |         sf.write(out_path, stereo_mix, self.sr, format="WAV", subtype="PCM_16")
```

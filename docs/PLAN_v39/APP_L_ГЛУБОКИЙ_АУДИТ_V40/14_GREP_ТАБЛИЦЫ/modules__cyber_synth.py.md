# grep-таблицы `modules/cyber_synth.py`

## `import` — 4 совпадений
```
    9 | from typing import Dict, Any
   10 | import numpy as np
   11 | import soundfile as sf
   14 |     from pedalboard import (
```

## `except` — 3 совпадений
```
   24 | except ImportError:
   71 |             except Exception:
  112 |             except Exception:
```

## `try` — 3 совпадений
```
   13 | try:
   64 |             try:
  105 |             try:
```

## `def` — 5 совпадений
```
   31 |     def __init__(self, sample_rate: int = 44100) -> None:
   34 |     def generate_sub_bass(self, freq: float, duration: float, decay: float = 4.0) -> np.ndarray:
   50 |     def generate_cyber_lead(self, freq: float, duration: float) -> np.ndarray:
   76 |     def synthesize_track(self, bpm: int = 135, duration_sec: int = 60, out_path: str = "cyber_track.wav") -> Dict[str, Any]:
  125 |     def sub_bass_pattern(self, root_freq: float, duration: float) -> np.ndarray:
```

## `class` — 1 совпадений
```
   28 | class CyberSynth:
```

## `return` — 4 совпадений
```
   48 |         return np.clip(bass, -1.0, 1.0)
   74 |         return np.clip(lead, -0.99, 0.99)
  118 |         return {
  134 |         return out
```

## `if` — 5 совпадений
```
   63 |         if HAS_PEDALBOARD:
   95 |             if current_sample + chunk_len <= total_samples:
  100 |             if current_sample >= total_samples:
  104 |         if HAS_PEDALBOARD:
  132 |         if len(hit) <= num_samples:
```

## `while` — 1 совпадений
```
   88 |         while current_sample < total_samples:
```

## `np` — 17 совпадений
```
   34 |     def generate_sub_bass(self, freq: float, duration: float, decay: float = 4.0) -> np.ndarray:
   37 |         time_vec = np.linspace(0, duration, num_samples, endpoint=False)
   40 |         freq_env = freq * (1.0 + 0.5 * np.exp(-time_vec * 15.0))
   41 |         phase = 2.0 * np.pi * np.cumsum(freq_env) / self.sr
   44 |         sub = 0.7 * np.sin(phase) + 0.3 * np.sin(phase * 0.5)
   45 |         amp_env = np.exp(-time_vec * decay)
   48 |         return np.clip(bass, -1.0, 1.0)
   50 |     def generate_cyber_lead(self, freq: float, duration: float) -> np.ndarray:
   53 |         time_vec = np.linspace(0, duration, num_samples, endpoint=False)
   57 |         modulator = np.sin(2.0 * np.pi * mod_freq * time_vec) * 3.0
   58 |         carrier = np.sin(2.0 * np.pi * freq * time_vec + modulator)
   60 |         env = np.exp(-time_vec * 2.0)
   74 |         return np.clip(lead, -0.99, 0.99)
   79 |         stereo_mix = np.zeros((total_samples, 2), dtype=np.float32)
  115 |         stereo_mix = np.clip(stereo_mix, -0.99, 0.99)
  125 |     def sub_bass_pattern(self, root_freq: float, duration: float) -> np.ndarray:
  128 |         out = np.zeros(num_samples, dtype=np.float32)
```

## `sf` — 1 совпадений
```
  116 |         sf.write(out_path, stereo_mix, self.sr, format="WAV", subtype="PCM_16")
```

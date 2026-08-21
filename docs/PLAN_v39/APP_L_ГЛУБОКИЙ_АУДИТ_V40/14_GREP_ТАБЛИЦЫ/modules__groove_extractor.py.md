# grep-таблицы `modules/groove_extractor.py`

## `import` — 5 совпадений
```
   11 | import json
   12 | import os
   14 | import numpy as np
   17 |     import librosa
  229 |     import sys
```

## `print` — 2 совпадений
```
  232 |         print("Usage: python groove_extractor.py <track.mp3>")
  234 |         print(json.dumps(extract_groove(sys.argv[1]), ensure_ascii=False, indent=2))
```

## `except` — 1 совпадений
```
   18 | except ImportError:
```

## `try` — 1 совпадений
```
   16 | try:
```

## `def` — 2 совпадений
```
   22 | def extract_groove(audio_path: str, bpm: float = None) -> dict:
  185 | def merge_grooves(grooves: list, weights: list = None) -> dict:
```

## `raise` — 1 совпадений
```
   35 |         raise RuntimeError("librosa не установлен")
```

## `return` — 5 совпадений
```
   90 |         return {"error": "Не удалось извлечь groove (слишком короткий трек)"}
  182 |     return groove_template
  188 |         return {}
  190 |         return grooves[0]
  215 |     return {
```

## `if` — 20 совпадений
```
   34 |     if librosa is None:
   40 |     if bpm is None:
   80 |         if end > total_frames:
   89 |     if not kick_pattern:
  110 |             if idx < len(kick_pattern):
  113 |     if swing_vals:
  118 |             if bar * steps_per_bar + step < len(kick_pattern)
  120 |         if even_vals and swing_vals:
  129 |     if n_bars > 0:
  135 |                 if idx + 2 < len(kick_binary):
  136 |                     if sum(kick_binary[idx : idx + 3]) >= 2:
  142 |     if n_bars >= 2:
  148 |             if prev_pat != curr_pat:
  158 |         if bar_end <= len(kick_pattern):
  161 |     if bar_energies:
  187 |     if not grooves:
  189 |     if len(grooves) == 1:
  192 |     if weights is None:
  228 | if __name__ == "__main__":
  231 |     if len(sys.argv) < 2:
```

## `for` — 12 совпадений
```
   77 |     for step in range(total_steps):
  106 |     for bar in range(n_bars):
  108 |         for step in range(0, steps_per_bar, 2):  # нечётные 16-е
  116 |             for bar in range(n_bars)
  117 |             for step in range(0, steps_per_bar, 2)
  131 |         for bar in range(min(n_bars, 4)):
  133 |             for step in range(steps_per_bar - 2):
  143 |         for bar in range(1, n_bars):
  155 |     for bar in range(n_bars):
  200 |     for g, w in zip(grooves, weights):
  203 |         for i in range(min(spb, len(kp))):
  205 |         for i in range(min(spb, len(sp))):
```

## `np` — 11 совпадений
```
   42 |         bpm = float(tempo) if np.ndim(tempo) == 0 else float(tempo[0])
   51 |     S = np.abs(librosa.stft(y, n_fft=1024, hop_length=512))
   63 |         S[hihat_mask].mean(axis=0) if hihat_mask.any() else np.zeros(S.shape[1])
   93 |     kick_thresh = np.mean(kick_pattern) + 0.3 * np.std(kick_pattern)
   94 |     snare_thresh = np.mean(snare_pattern) + 0.3 * np.std(snare_pattern)
   99 |     hihat_mean = float(np.mean(hihat_pattern)) if hihat_pattern else 0
  100 |     hihat_std = float(np.std(hihat_pattern)) if hihat_pattern else 0
  123 |                 abs(np.mean(swing_vals) - np.mean(even_vals))
  124 |                 / (np.mean(even_vals) + 1e-9),
  159 |             bar_energies.append(float(np.mean(kick_pattern[bar_start:bar_end])))
  163 |             1.0, max(bar_energies) / (np.mean(bar_energies) + 1e-9) - 1.0
```

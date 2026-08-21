# grep-таблицы `modules/female_backing.py`

## `import` — 18 совпадений
```
   15 | from __future__ import annotations
   17 | from pathlib import Path
   27 |         import torch
   45 |         import soundfile as sf
   56 |         import soundfile as sf
   57 |         from bark import SAMPLE_RATE, generate_audio
   69 |         import pyttsx3
   96 |         import numpy as np
   97 |         import soundfile as sf
  114 |         import numpy as np
  115 |         import soundfile as sf
  123 |             import librosa
  136 |             from scipy.signal import butter, sosfilt
  163 |         import numpy as np
  164 |         import soundfile as sf
  197 |         import numpy as np
  198 |         import soundfile as sf
  208 |                 import librosa
```

## `print` — 6 совпадений
```
   50 |         print(f"[female_backing] silero failed: {e}")
   63 |         print(f"[female_backing] bark failed: {e}")
   84 |         print(f"[female_backing] pyttsx failed: {e}")
  151 |         print(f"[female_backing] sweeten failed: {e}")
  186 |         print(f"[female_backing] make_chorus_backing failed: {e}")
  224 |         print(f"[female_backing] mix failed: {e}")
```

## `except` — 12 совпадений
```
   40 |             except Exception:
   49 |     except Exception as e:
   62 |     except Exception as e:
   83 |     except Exception as e:
  100 |     except Exception:
  131 |         except Exception:
  141 |         except Exception:
  150 |     except Exception as e:
  177 |             except Exception:
  185 |     except Exception as e:
  211 |             except Exception:
  223 |     except Exception as e:
```

## `try` — 12 совпадений
```
   26 |     try:
   38 |             try:
   55 |     try:
   68 |     try:
   95 |     try:
  113 |     try:
  122 |         try:
  135 |         try:
  162 |     try:
  170 |             try:
  196 |     try:
  207 |             try:
```

## `def` — 7 совпадений
```
   25 | def _synth_silero(text: str, out_wav: Path, speaker: str = "kseniya") -> bool:
   54 | def _synth_bark(text: str, out_wav: Path) -> bool:
   67 | def _synth_pyttsx(text: str, out_wav: Path) -> bool:
   88 | def synth_female_line(text: str, out_wav: Path | None = None) -> Path:
  106 | def sweeten_backing(
  156 | def make_chorus_backing(chorus_lines: list[str], out_wav: Path | None = None) -> Path:
  190 | def mix_backing_into_vocal(
```

## `return` — 15 совпадений
```
   48 |         return True
   51 |         return False
   61 |         return True
   64 |         return False
   82 |         return out_wav.exists() and out_wav.stat().st_size > 500
   85 |         return False
   93 |             return out_wav
  102 |     return out_wav
  149 |         return out
  152 |         return wav_path
  181 |             return out_wav
  184 |         return sweeten_backing(out_wav)
  187 |         return out_wav
  222 |         return out
  225 |         return main_vocal_wav
```

## `if` — 11 совпадений
```
   30 |         if not model_path.exists():
   73 |             if (
   92 |         if backend(text, out_wav):
  118 |         if y.ndim == 1:
  172 |                 if y.ndim == 1:
  179 |         if not chunks:
  202 |         if v.ndim == 1:
  204 |         if b.ndim == 1:
  206 |         if sr2 != sr:
  214 |         if len(v) < n:
  216 |         if len(b) < n:
```

## `for` — 4 совпадений
```
   72 |         for v in eng.getProperty("voices"):
   91 |     for backend in (_synth_silero, _synth_bark, _synth_pyttsx):
  139 |             for ch in range(y.shape[1]):
  168 |         for line in chorus_lines[:8]:
```

## `np` — 12 совпадений
```
   99 |         sf.write(str(out_wav), np.zeros(int(48000 * 0.5)), 48000)
  119 |             y = np.stack([y, y], axis=-1)
  130 |             y = np.stack([shifted, shifted], axis=-1)
  173 |                     y = np.stack([y, y], axis=-1)
  176 |                 chunks.append(np.zeros((sr // 4, 2)))
  180 |             sf.write(str(out_wav), np.zeros((sr, 2)), sr)
  182 |         big = np.concatenate(chunks, axis=0)
  203 |             v = np.stack([v, v], axis=-1)
  205 |             b = np.stack([b, b], axis=-1)
  215 |             v = np.pad(v, ((0, n - len(v)), (0, 0)))
  217 |             b = np.pad(b, ((0, n - len(b)), (0, 0)))
  219 |         mixed = np.clip(v + b, -1.0, 1.0)
```

## `sf` — 11 совпадений
```
   47 |         sf.write(str(out_wav), audio.cpu().numpy(), 48000)
   60 |         sf.write(str(out_wav), arr, SAMPLE_RATE)
   99 |         sf.write(str(out_wav), np.zeros(int(48000 * 0.5)), 48000)
  117 |         y, sr = sf.read(str(wav_path))
  148 |         sf.write(str(out), y, sr)
  171 |                 y, sr = sf.read(str(p))
  180 |             sf.write(str(out_wav), np.zeros((sr, 2)), sr)
  183 |         sf.write(str(out_wav), big, sr)
  200 |         v, sr = sf.read(str(main_vocal_wav))
  201 |         b, sr2 = sf.read(str(backing_wav))
  221 |         sf.write(str(out), mixed, sr)
```

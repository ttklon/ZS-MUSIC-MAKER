# grep-таблицы `modules/voice_cleaner.py`

## `import` — 5 совпадений
```
    8 | import os
    9 | import shutil
   11 | import soundfile as sf
   18 |     import noisereduce as nr  # type: ignore
   29 |     import numpy as np
```

## `except` — 2 совпадений
```
   20 | except Exception:  # pragma: no cover
   75 |     except Exception:
```

## `try` — 2 совпадений
```
   17 | try:
   72 |     try:
```

## `def` — 2 совпадений
```
   25 | def _fallback_clean(data, samplerate):
   52 | def clean_vocal(input_wav: str, output_wav: str, prop_decrease: float = 1.0):
```

## `return` — 3 совпадений
```
   49 |     return y[:, 0] if mono else y
   64 |         return {
   77 |     return {
```

## `if` — 3 совпадений
```
   33 |     if mono:
   60 |     if _HAS_NR:
   87 | if __name__ == "__main__":
```

## `for` — 1 совпадений
```
   44 |     for n in range(len(x)):
```

## `np` — 4 совпадений
```
   31 |     x = np.asarray(data, dtype=np.float32)
   36 |     x = x - np.mean(x, axis=0, keepdims=True)
   41 |     y = np.zeros_like(x)
   43 |     prev_y = np.zeros(x.shape[1], dtype=np.float32)
```

## `sf` — 3 совпадений
```
   56 |     data, samplerate = sf.read(input_wav)
   63 |         sf.write(output_wav, reduced_noise, samplerate)
   74 |         sf.write(output_wav, cleaned, samplerate)
```

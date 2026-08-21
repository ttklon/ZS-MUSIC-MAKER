# grep-таблицы `modules/stem_splitter.py`

## `import` — 6 совпадений
```
    7 | import os
    8 | import subprocess
    9 | import sys
   18 |         import demucs.separate  # noqa
   56 |         import librosa
   57 |         import numpy as np
```

## `print` — 2 совпадений
```
   73 |         print("Usage: python stem_splitter.py <track.mp3>")
   75 |         print(split_stems(sys.argv[1]))
```

## `except` — 3 совпадений
```
   19 |     except ImportError:
   35 |     except subprocess.CalledProcessError as e:
   58 |     except ImportError:
```

## `try` — 3 совпадений
```
   17 |     try:
   33 |     try:
   55 |     try:
```

## `def` — 2 совпадений
```
   14 | def split_stems(input_path: str, model: str = "htdemucs") -> dict:
   53 | def analyze_arrangement(stems: dict) -> dict:
```

## `return` — 5 совпадений
```
   20 |         return {"error": "Demucs не установлен. pip install demucs"}
   36 |         return {"error": f"Demucs failed: {e}"}
   50 |     return result
   59 |         return {"error": "librosa не установлен"}
   68 |     return report
```

## `if` — 4 совпадений
```
   44 |             if os.path.exists(p):
   63 |         if not p or not os.path.exists(p):
   71 | if __name__ == "__main__":
   72 |     if len(sys.argv) < 2:
```

## `for` — 3 совпадений
```
   41 |     for stem in ["vocals", "drums", "bass", "other"]:
   42 |         for ext in ("mp3", "wav"):
   61 |     for name in ["vocals", "drums", "bass", "other"]:
```

## `subprocess` — 2 совпадений
```
   34 |         subprocess.run(cmd, check=True)
   35 |     except subprocess.CalledProcessError as e:
```

## `np` — 1 совпадений
```
   66 |         rms = float(np.mean(librosa.feature.rms(y=y)))
```

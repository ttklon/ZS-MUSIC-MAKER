# grep-таблицы `tools/validate_final_track.py`

## `import` — 5 совпадений
```
   12 | import sys
   13 | from pathlib import Path
   17 | from tests.test_audio_quality import validate_audio_file
   18 | import soundfile as sf
   19 | import numpy as np
```

## `print` — 11 совпадений
```
   35 |             print("USAGE: python tools/validate_final_track.py <path/to/track.wav>")
   36 |             print("(мастера в output/**/masters/*.wav не найдены)")
   40 |     print(f"--- Final Quality Audit for: {track_path} ---")
   51 |         print("STATUS: PASS ✅")
   52 |         print(f"Peak Level: {peak:.4f} (Target <= 1.0)")
   53 |         print(f"RMS Level: {rms:.4f}")
   54 |         print(f"Duration: {duration:.2f}s")
   55 |         print(f"Sample Rate: {sr}Hz")
   56 |         print(f"Channels: {channels}")
   59 |         print("STATUS: FAIL ❌")
   60 |         print(f"Error: {e}")
```

## `except` — 1 совпадений
```
   58 |     except Exception as e:
```

## `try` — 1 совпадений
```
   41 |     try:
```

## `def` — 2 совпадений
```
   24 | def _find_latest_master() -> Path | None:
   29 | def main() -> int:
```

## `raise` — 1 совпадений
```
   43 |             raise FileNotFoundError(f"File not found: {track_path}")
```

## `return` — 4 совпадений
```
   26 |     return masters[-1] if masters else None
   37 |             return 2
   57 |         return 0
   61 |         return 1
```

## `if` — 4 совпадений
```
   30 |     if len(sys.argv) > 1:
   34 |         if not found:
   42 |         if not track_path.exists():
   64 | if __name__ == "__main__":
```

## `path_home` — 1 совпадений
```
    4 | /home/ubuntu/ZS-MUSIC-MAKER/... — на любой другой машине инструмент всегда
```

## `np` — 2 совпадений
```
   46 |         peak = float(np.max(np.abs(data)))
   47 |         rms = float(np.sqrt(np.mean(data**2)))
```

## `sf` — 1 совпадений
```
   45 |         data, sr = sf.read(str(track_path))
```

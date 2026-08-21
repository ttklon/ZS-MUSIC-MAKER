# grep-таблицы `modules/mixdown.py`

## `import` — 8 совпадений
```
   10 | import os
   11 | import shutil
   13 | import numpy as np
   27 |     from pydub import AudioSegment
   58 |         from scipy.io import wavfile
   59 |         from scipy.signal import butter, sosfilt
  107 |         import matchering as mg
  126 |         from pydub import AudioSegment
```

## `print` — 3 совпадений
```
  119 |         print("[matchering] MISSING — fallback: copy")
  122 |         print(f"[matchering error] {e} — fallback: copy")
  177 |     print("mixdown module ready v2")
```

## `except` — 4 совпадений
```
   60 |     except ImportError:
  117 |     except ImportError:
  120 |     except Exception as e:
  130 |     except Exception:
```

## `try` — 3 совпадений
```
   57 |     try:
  106 |     try:
  125 |     try:
```

## `def` — 5 совпадений
```
   19 | def mix_beat_and_vocal(
   50 | def apply_eq(
   90 | def master_with_matchering(
   98 | def master_with_matchering_status(
  143 | def full_mixdown(
```

## `return` — 6 совпадений
```
   47 |     return out
   61 |         return audio_path
   87 |     return out
   95 |     return res["master_wav"]
  133 |     return {
  161 |     return {
```

## `if` — 8 совпадений
```
   33 |     if len(vocal) < len(beat):
   64 |     if data.ndim > 1:
   69 |     if low_cut_hz > 0:
   74 |     if high_shelf_db != 0:
   81 |     if peak > 1.0:
  156 |     if apply_eq_enabled:
  166 |             if os.path.exists(master.replace(".wav", ".mp3"))
  176 | if __name__ == "__main__":
```

## `np` — 3 совпадений
```
   66 |     data = data.astype(np.float32) / (2**15)
   80 |     peak = np.max(np.abs(data)) + 1e-9
   86 |     wavfile.write(out, sr, (data * 32767).astype(np.int16))
```

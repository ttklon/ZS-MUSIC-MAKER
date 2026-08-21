# grep-таблицы `modules/musical_intelligence.py`

## `import` — 6 совпадений
```
    9 | import os
   10 | import numpy as np
   14 |     from pyAudioAnalysis import audioBasicIO
   15 |     from pyAudioAnalysis import ShortTermFeatures
   21 |     import mingus.core.chords as chords
   22 |     import mingus.core.keys as keys
```

## `print` — 1 совпадений
```
   90 |     print(intel.suggest_chords("A", "minor"))
```

## `except` — 4 совпадений
```
   17 | except ImportError:
   24 | except ImportError:
   66 |         except Exception as e:
   84 |         except Exception:
```

## `try` — 4 совпадений
```
   13 | try:
   20 | try:
   42 |         try:
   75 |         try:
```

## `def` — 3 совпадений
```
   29 |     def __init__(self, sr: int = 44100):
   32 |     def analyze_key(self, wav_path: str) -> dict:
   69 |     def suggest_chords(self, key_root: str, mode: str) -> list:
```

## `class` — 1 совпадений
```
   28 | class MusicalIntelligence:
```

## `return` — 7 совпадений
```
   37 |             return {"ok": False, "error": "File not found"}
   40 |             return {"ok": True, "key": "A minor", "root": "A", "mode": "minor", "fallback": True}
   59 |             return {
   67 |             return {"ok": False, "error": str(e)}
   74 |             return [["Am"], ["F"], ["C"], ["G"]]
   83 |             return [chords.triads(n, key_root + ("m" if mode == "minor" else "")) for n in prog]
   85 |             return [["Am"], ["F"], ["C"], ["G"]]
```

## `if` — 6 совпадений
```
   36 |         if not os.path.exists(wav_path):
   39 |         if not HAS_PYAUDIO:
   44 |             if x.ndim > 1:
   73 |         if not HAS_MINGUS:
   76 |             if mode == "minor":
   88 | if __name__ == "__main__":
```

## `np` — 1 совпадений
```
   51 |             dominant_note_idx = np.argmax(chroma)
```

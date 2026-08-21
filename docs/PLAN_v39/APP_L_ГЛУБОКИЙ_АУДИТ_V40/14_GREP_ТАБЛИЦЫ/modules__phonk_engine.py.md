# grep-таблицы `modules/phonk_engine.py`

## `import` — 2 совпадений
```
    4 | import numpy as np
   11 |     import soundfile as sf
```

## `def` — 1 совпадений
```
    6 | def generate_cowbell(notes: list, bpm: int, out_path: str) -> str:
```

## `return` — 1 совпадений
```
   13 |     return out_path
```

## `np` — 2 совпадений
```
    9 |     t = np.linspace(0, 0.2, int(sr * 0.2))
   10 |     audio = np.sin(2 * np.pi * 800 * t) * np.exp(-t * 15)
```

## `sf` — 1 совпадений
```
   12 |     sf.write(out_path, audio, sr)
```

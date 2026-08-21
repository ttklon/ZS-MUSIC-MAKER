# grep-таблицы `app/plugins/advanced.py`

## `import` — 4 совпадений
```
    8 | import numpy as np
    9 | from app.plugins.base import AudioPlugin
   14 |     from pedalboard import Pedalboard, Distortion, Reverb, Compressor, HighpassFilter  # type: ignore
   33 |     from audiomentations import Compose, PitchShift, TimeStretch, AddGaussianNoise, RoomSimulator  # type: ignore
```

## `except` — 2 совпадений
```
   16 | except Exception:  # pragma: no cover
   35 | except Exception:  # pragma: no cover
```

## `try` — 2 совпадений
```
   13 | try:
   32 | try:
```

## `def` — 10 совпадений
```
   20 |         def __init__(self, *a, **k):
   24 |         def __init__(self, effects=None):
   27 |         def __call__(self, audio, sr):
   39 |         def __init__(self, transforms=None):
   42 |         def __call__(self, samples, sample_rate):
   48 |     def __init__(self, name: str, effects: list):
   52 |     def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
   62 |     def __init__(self, drive_db: float = 20.0):
   70 |     def __init__(self, intensity: float = 0.5):
   79 |     def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
```

## `class` — 6 совпадений
```
   19 |     class _NoopFx:  # минимальная заглушка, не ломающая сборку
   23 |     class Pedalboard:  # type: ignore
   38 |     class Compose:  # type: ignore
   47 | class PedalboardPlugin(AudioPlugin):
   61 | class PhonkDistortion(PedalboardPlugin):
   69 | class AntiAINeuroObfuscator(AudioPlugin):
```

## `return` — 6 совпадений
```
   28 |             return audio  # passthrough
   43 |             return samples  # passthrough
   57 |             return processed.T
   59 |             return self.board(audio, sr)
   84 |             return processed.T
   86 |             return self.augment(samples=audio, sample_rate=sr)
```

## `if` — 2 совпадений
```
   54 |         if audio.ndim == 2:
   81 |         if audio.ndim == 2:
```

## `np` — 2 совпадений
```
   52 |     def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
   79 |     def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
```

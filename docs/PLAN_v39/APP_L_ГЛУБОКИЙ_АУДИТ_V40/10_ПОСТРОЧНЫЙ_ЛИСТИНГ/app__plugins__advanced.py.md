# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/plugins/advanced.py`

**Всего строк:** 86

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 27 | 31.4 |
| blank | 15 | 17.4 |
| def | 10 | 11.6 |
| class | 6 | 7.0 |
| return | 6 | 7.0 |
| comment | 5 | 5.8 |
| docstring | 5 | 5.8 |
| import | 4 | 4.7 |
| try_block | 4 | 4.7 |
| branch | 4 | 4.7 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — plugins/advanced.py (GOD MODE)
    4 [docstring ] ========================================================================
    5 [docstring ] Продвинутые плагины: сатурация, пространственные эффекты и Anti-AI аугментация.
    6 [docstring ] """
    7 [blank     ] 
    8 [import    ] import numpy as np
    9 [import    ] from app.plugins.base import AudioPlugin
   10 [blank     ] 
   11 [comment   ] # v27 FIX (P0): pedalboard / audiomentations были жёсткими top-level импортами —
   12 [comment   ] # без них падал весь plugin-слой. Теперь ленивые, с честными no-op заглушками.
   13 [try_block ] try:
   14 [import    ]     from pedalboard import Pedalboard, Distortion, Reverb, Compressor, HighpassFilter  # type: ignore
   15 [code      ]     _HAS_PB = True
   16 [try_block ] except Exception:  # pragma: no cover
   17 [code      ]     _HAS_PB = False
   18 [blank     ] 
   19 [class     ]     class _NoopFx:  # минимальная заглушка, не ломающая сборку
   20 [def       ]         def __init__(self, *a, **k):
   21 [code      ]             pass
   22 [blank     ] 
   23 [class     ]     class Pedalboard:  # type: ignore
   24 [def       ]         def __init__(self, effects=None):
   25 [code      ]             self.effects = effects or []
   26 [blank     ] 
   27 [def       ]         def __call__(self, audio, sr):
   28 [return    ]             return audio  # passthrough
   29 [blank     ] 
   30 [code      ]     Distortion = Reverb = Compressor = HighpassFilter = _NoopFx  # type: ignore
   31 [blank     ] 
   32 [try_block ] try:
   33 [import    ]     from audiomentations import Compose, PitchShift, TimeStretch, AddGaussianNoise, RoomSimulator  # type: ignore
   34 [code      ]     _HAS_AUG = True
   35 [try_block ] except Exception:  # pragma: no cover
   36 [code      ]     _HAS_AUG = False
   37 [blank     ] 
   38 [class     ]     class Compose:  # type: ignore
   39 [def       ]         def __init__(self, transforms=None):
   40 [code      ]             self.transforms = transforms or []
   41 [blank     ] 
   42 [def       ]         def __call__(self, samples, sample_rate):
   43 [return    ]             return samples  # passthrough
   44 [blank     ] 
   45 [code      ]     PitchShift = TimeStretch = AddGaussianNoise = RoomSimulator = object  # type: ignore
   46 [blank     ] 
   47 [class     ] class PedalboardPlugin(AudioPlugin):
   48 [def       ]     def __init__(self, name: str, effects: list):
   49 [code      ]         super().__init__(name)
   50 [code      ]         self.board = Pedalboard(effects)
   51 [blank     ] 
   52 [def       ]     def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
   53 [comment   ]         # Pedalboard expects (channels, frames)
   54 [branch    ]         if audio.ndim == 2:
   55 [code      ]             audio_t = audio.T
   56 [code      ]             processed = self.board(audio_t, sr)
   57 [return    ]             return processed.T
   58 [branch    ]         else:
   59 [return    ]             return self.board(audio, sr)
   60 [blank     ] 
   61 [class     ] class PhonkDistortion(PedalboardPlugin):
   62 [def       ]     def __init__(self, drive_db: float = 20.0):
   63 [code      ]         super().__init__("PhonkDistortion", [
   64 [code      ]             Distortion(drive_db=drive_db),
   65 [code      ]             HighpassFilter(cutoff_frequency_hz=300),
   66 [code      ]             Compressor(threshold_db=-15, ratio=4.0)
   67 [code      ]         ])
   68 [blank     ] 
   69 [class     ] class AntiAINeuroObfuscator(AudioPlugin):
   70 [def       ]     def __init__(self, intensity: float = 0.5):
   71 [code      ]         super().__init__("AntiAINeuroObfuscator")
   72 [code      ]         self.augment = Compose([
   73 [code      ]             PitchShift(min_semitones=-0.2, max_semitones=0.2, p=intensity),
   74 [code      ]             TimeStretch(min_rate=0.98, max_rate=1.02, p=intensity),
   75 [code      ]             AddGaussianNoise(min_amplitude=0.001, max_amplitude=0.005, p=intensity * 0.5),
   76 [code      ]             RoomSimulator(p=intensity * 0.3)
   77 [code      ]         ])
   78 [blank     ] 
   79 [def       ]     def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
   80 [comment   ]         # Audiomentations expects (channels, frames) or (frames,)
   81 [branch    ]         if audio.ndim == 2:
   82 [code      ]             audio_t = audio.T
   83 [code      ]             processed = self.augment(samples=audio_t, sample_rate=sr)
   84 [return    ]             return processed.T
   85 [branch    ]         else:
   86 [return    ]             return self.augment(samples=audio, sample_rate=sr)
```
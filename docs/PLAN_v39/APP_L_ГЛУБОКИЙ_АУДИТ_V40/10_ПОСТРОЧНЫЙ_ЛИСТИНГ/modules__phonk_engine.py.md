# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/phonk_engine.py`

**Всего строк:** 13

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| docstring | 4 | 30.8 |
| code | 4 | 30.8 |
| import | 2 | 15.4 |
| blank | 1 | 7.7 |
| def | 1 | 7.7 |
| return | 1 | 7.7 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] Legacy phonk_engine compatibility shim for phonk_engine_v2.py
    3 [docstring ] """
    4 [import    ] import numpy as np
    5 [blank     ] 
    6 [def       ] def generate_cowbell(notes: list, bpm: int, out_path: str) -> str:
    7 [docstring ]     """Generates a simple cowbell sample."""
    8 [code      ]     sr = 44100
    9 [code      ]     t = np.linspace(0, 0.2, int(sr * 0.2))
   10 [code      ]     audio = np.sin(2 * np.pi * 800 * t) * np.exp(-t * 15)
   11 [import    ]     import soundfile as sf
   12 [code      ]     sf.write(out_path, audio, sr)
   13 [return    ]     return out_path
```
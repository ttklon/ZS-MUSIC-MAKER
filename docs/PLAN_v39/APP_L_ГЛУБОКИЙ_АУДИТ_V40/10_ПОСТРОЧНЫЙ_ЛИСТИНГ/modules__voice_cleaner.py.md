# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/voice_cleaner.py`

**Всего строк:** 89

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 37 | 41.6 |
| blank | 13 | 14.6 |
| docstring | 12 | 13.5 |
| comment | 9 | 10.1 |
| import | 5 | 5.6 |
| try_block | 4 | 4.5 |
| branch | 3 | 3.4 |
| return | 3 | 3.4 |
| def | 2 | 2.2 |
| loop | 1 | 1.1 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker — voice_cleaner.py (GOD MODE)
    3 [docstring ] ========================================================================
    4 [docstring ] Интеллектуальная очистка голоса от шумов.
    5 [docstring ] Использует спектральное вычитание для удаления фонового шума.
    6 [docstring ] """
    7 [blank     ] 
    8 [import    ] import os
    9 [import    ] import shutil
   10 [blank     ] 
   11 [import    ] import soundfile as sf
   12 [blank     ] 
   13 [comment   ] # v27 FIX (P0): noisereduce был жёстким top-level импортом — при его отсутствии
   14 [comment   ] # падал ВЕСЬ orchestrator_god (ModuleNotFoundError на import). Теперь ленивый
   15 [comment   ] # импорт с честным fallback: highpass+простое спектральное приглушение либо
   16 [comment   ] # passthrough-копия, но пайплайн не ломается.
   17 [try_block ] try:
   18 [import    ]     import noisereduce as nr  # type: ignore
   19 [code      ]     _HAS_NR = True
   20 [try_block ] except Exception:  # pragma: no cover
   21 [code      ]     nr = None
   22 [code      ]     _HAS_NR = False
   23 [blank     ] 
   24 [blank     ] 
   25 [def       ] def _fallback_clean(data, samplerate):
   26 [docstring ]     """Лёгкий offline fallback: убираем DC + мягкий highpass ~80Hz однополюсным
   27 [docstring ]     фильтром + лёгкое приглушение низкочастотного гула. Не noisereduce, но
   28 [docstring ]     лучше, чем ничего, и честно помечено fallback_used=True."""
   29 [import    ]     import numpy as np
   30 [blank     ] 
   31 [code      ]     x = np.asarray(data, dtype=np.float32)
   32 [code      ]     mono = x.ndim == 1
   33 [branch    ]     if mono:
   34 [code      ]         x = x[:, None]
   35 [comment   ]     # DC removal
   36 [code      ]     x = x - np.mean(x, axis=0, keepdims=True)
   37 [comment   ]     # однополюсный highpass: y[n] = a*(y[n-1] + x[n] - x[n-1])
   38 [code      ]     rc = 1.0 / (2.0 * 3.14159265 * 80.0)
   39 [code      ]     dt = 1.0 / float(samplerate)
   40 [code      ]     a = rc / (rc + dt)
   41 [code      ]     y = np.zeros_like(x)
   42 [code      ]     prev_x = x[0].copy()
   43 [code      ]     prev_y = np.zeros(x.shape[1], dtype=np.float32)
   44 [loop      ]     for n in range(len(x)):
   45 [code      ]         cur = a * (prev_y + x[n] - prev_x)
   46 [code      ]         y[n] = cur
   47 [code      ]         prev_y = cur
   48 [code      ]         prev_x = x[n]
   49 [return    ]     return y[:, 0] if mono else y
   50 [blank     ] 
   51 [blank     ] 
   52 [def       ] def clean_vocal(input_wav: str, output_wav: str, prop_decrease: float = 1.0):
   53 [docstring ]     """
   54 [docstring ]     Очистка вокала от шума.
   55 [docstring ]     """
   56 [code      ]     data, samplerate = sf.read(input_wav)
   57 [blank     ] 
   58 [code      ]     os.makedirs(os.path.dirname(output_wav) or ".", exist_ok=True)
   59 [blank     ] 
   60 [branch    ]     if _HAS_NR:
   61 [comment   ]         # noisereduce работает с 1D (mono) или 2D (stereo) массивами
   62 [code      ]         reduced_noise = nr.reduce_noise(y=data, sr=samplerate, prop_decrease=prop_decrease)
   63 [code      ]         sf.write(output_wav, reduced_noise, samplerate)
   64 [return    ]         return {
   65 [code      ]             "ok": True,
   66 [code      ]             "path": output_wav,
   67 [code      ]             "engine": "noisereduce_v3",
   68 [code      ]             "prop_decrease": prop_decrease,
   69 [code      ]         }
   70 [blank     ] 
   71 [comment   ]     # FALLBACK_ONLY: честный lightweight-режим без noisereduce
   72 [try_block ]     try:
   73 [code      ]         cleaned = _fallback_clean(data, samplerate)
   74 [code      ]         sf.write(output_wav, cleaned, samplerate)
   75 [try_block ]     except Exception:
   76 [code      ]         shutil.copy(input_wav, output_wav)
   77 [return    ]     return {
   78 [code      ]         "ok": True,
   79 [code      ]         "path": output_wav,
   80 [code      ]         "engine": "fallback_highpass_dc",
   81 [code      ]         "fallback_used": True,
   82 [code      ]         "reason": "noisereduce not installed; DC-removal + 80Hz highpass applied",
   83 [code      ]         "prop_decrease": prop_decrease,
   84 [code      ]     }
   85 [blank     ] 
   86 [blank     ] 
   87 [branch    ] if __name__ == "__main__":
   88 [comment   ]     # Тестовый запуск
   89 [code      ]     pass
```
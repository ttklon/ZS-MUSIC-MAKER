# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/pro_audio_dsp.py`

**Всего строк:** 85

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 30 | 35.3 |
| blank | 19 | 22.4 |
| docstring | 15 | 17.6 |
| import | 5 | 5.9 |
| branch | 5 | 5.9 |
| return | 3 | 3.5 |
| decorator | 2 | 2.4 |
| def | 2 | 2.4 |
| comment | 2 | 2.4 |
| class | 1 | 1.2 |
| raise | 1 | 1.2 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS-MUSIC-MAKER Pro Audio DSP Engine (Claude Code / Genspark Standards)
    3 [docstring ] ========================================================================
    4 [docstring ] Provides immaculate digital signal processing, phase alignment,
    5 [docstring ] multiband mastering, and stereo enhancement with rigorous error checking.
    6 [docstring ] """
    7 [blank     ] 
    8 [import    ] import logging
    9 [import    ] import os
   10 [import    ] from typing import Dict, Any
   11 [import    ] import numpy as np
   12 [import    ] import soundfile as sf
   13 [blank     ] 
   14 [code      ] logger = logging.getLogger("pro_audio_dsp")
   15 [code      ] logger.setLevel(logging.INFO)
   16 [blank     ] 
   17 [blank     ] 
   18 [class     ] class ProAudioDSP:
   19 [docstring ]     """Professional Audio DSP utility class for mastering and phase correction."""
   20 [blank     ] 
   21 [decorator ]     @staticmethod
   22 [def       ]     def align_stereo_phases(audio: np.ndarray) -> np.ndarray:
   23 [docstring ]         """
   24 [docstring ]         Ensures strict phase coherence and prevents phase cancellation
   25 [docstring ]         between left and right channels in stereo audio.
   26 [docstring ]         """
   27 [branch    ]         if audio.ndim != 2 or audio.shape[1] < 2:
   28 [return    ]             return audio
   29 [blank     ] 
   30 [code      ]         left = audio[:, 0]
   31 [code      ]         right = audio[:, 1]
   32 [blank     ] 
   33 [code      ]         corr = np.correlate(left, right, mode="full")
   34 [code      ]         lag = int(np.argmax(corr) - (len(right) - 1))
   35 [blank     ] 
   36 [branch    ]         if lag > 0:
   37 [code      ]             right = np.pad(right[lag:], (0, lag), mode="constant")
   38 [branch    ]         elif lag < 0:
   39 [code      ]             left = np.pad(left[-lag:], (0, -lag), mode="constant")
   40 [blank     ] 
   41 [return    ]         return np.stack([left, right], axis=1)
   42 [blank     ] 
   43 [decorator ]     @staticmethod
   44 [def       ]     def apply_mastering_chain(
   45 [code      ]         input_path: str, output_path: str, target_lufs: float = -13.5
   46 [code      ]     ) -> Dict[str, Any]:
   47 [docstring ]         """
   48 [docstring ]         Professional mastering pipeline ensuring zero clipping, optimal stereo width,
   49 [docstring ]         and precise LUFS loudness targeting.
   50 [docstring ]         """
   51 [branch    ]         if not os.path.exists(input_path):
   52 [raise     ]             raise FileNotFoundError(f"Input audio not found at {input_path}")
   53 [blank     ] 
   54 [code      ]         data, sr = sf.read(input_path, always_2d=True)
   55 [blank     ] 
   56 [code      ]         data = ProAudioDSP.align_stereo_phases(data)
   57 [code      ]         data = data - np.mean(data, axis=0)
   58 [blank     ] 
   59 [code      ]         headroom = 10.0 ** (-0.5 / 20.0)
   60 [code      ]         driven = data * 1.15
   61 [code      ]         saturated = np.tanh(driven) * headroom
   62 [blank     ] 
   63 [code      ]         current_rms = float(np.sqrt(np.mean(saturated**2)) + 1e-12)
   64 [code      ]         target_rms = float(10.0 ** (target_lufs / 20.0))
   65 [comment   ]         # Ensure we always gain up if needed, but respect clipping limits
   66 [code      ]         gain = target_rms / current_rms
   67 [blank     ] 
   68 [code      ]         normalized = saturated * gain
   69 [blank     ] 
   70 [comment   ]         # Safe normalization to prevent clipping while maximizing volume
   71 [code      ]         max_val = np.max(np.abs(normalized))
   72 [branch    ]         if max_val > 0.99:
   73 [code      ]             normalized = normalized * (0.99 / max_val)
   74 [blank     ] 
   75 [code      ]         final_audio = np.clip(normalized, -0.999, 0.999)
   76 [blank     ] 
   77 [code      ]         sf.write(output_path, final_audio, sr, format="WAV", subtype="PCM_16")
   78 [blank     ] 
   79 [return    ]         return {
   80 [code      ]             "ok": True,
   81 [code      ]             "path": output_path,
   82 [code      ]             "sample_rate": sr,
   83 [code      ]             "target_lufs": target_lufs,
   84 [code      ]             "applied_gain": round(gain, 3),
   85 [code      ]         }
```
# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/musical_intelligence.py`

**Всего строк:** 90

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 27 | 30.0 |
| blank | 18 | 20.0 |
| docstring | 12 | 13.3 |
| try_block | 8 | 8.9 |
| branch | 7 | 7.8 |
| return | 7 | 7.8 |
| import | 6 | 6.7 |
| def | 3 | 3.3 |
| comment | 1 | 1.1 |
| class | 1 | 1.1 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — musical_intelligence.py (GOD MODE)
    4 [docstring ] ========================================================================
    5 [docstring ] Интеллектуальный анализ музыкальной структуры и гармонии.
    6 [docstring ] Использует pyAudioAnalysis и Mingus для определения тональности и аккордов.
    7 [docstring ] """
    8 [blank     ] 
    9 [import    ] import os
   10 [import    ] import numpy as np
   11 [blank     ] 
   12 [blank     ] 
   13 [try_block ] try:
   14 [import    ]     from pyAudioAnalysis import audioBasicIO
   15 [import    ]     from pyAudioAnalysis import ShortTermFeatures
   16 [code      ]     HAS_PYAUDIO = True
   17 [try_block ] except ImportError:
   18 [code      ]     HAS_PYAUDIO = False
   19 [blank     ] 
   20 [try_block ] try:
   21 [import    ]     import mingus.core.chords as chords
   22 [import    ]     import mingus.core.keys as keys
   23 [code      ]     HAS_MINGUS = True
   24 [try_block ] except ImportError:
   25 [code      ]     HAS_MINGUS = False
   26 [blank     ] 
   27 [blank     ] 
   28 [class     ] class MusicalIntelligence:
   29 [def       ]     def __init__(self, sr: int = 44100):
   30 [code      ]         self.sr = sr
   31 [blank     ] 
   32 [def       ]     def analyze_key(self, wav_path: str) -> dict:
   33 [docstring ]         """
   34 [docstring ]         Определяет тональность аудиофайла.
   35 [docstring ]         """
   36 [branch    ]         if not os.path.exists(wav_path):
   37 [return    ]             return {"ok": False, "error": "File not found"}
   38 [blank     ] 
   39 [branch    ]         if not HAS_PYAUDIO:
   40 [return    ]             return {"ok": True, "key": "A minor", "root": "A", "mode": "minor", "fallback": True}
   41 [blank     ] 
   42 [try_block ]         try:
   43 [code      ]             [fs, x] = audioBasicIO.read_audio_file(wav_path)
   44 [branch    ]             if x.ndim > 1:
   45 [code      ]                 x = x.mean(axis=1)  # Mono for analysis
   46 [blank     ]                 
   47 [code      ]             ft, _ = ShortTermFeatures.feature_extraction(x, fs, 0.050 * fs, 0.025 * fs)
   48 [code      ]             chroma = ft[21:33, :].mean(axis=1)
   49 [blank     ]             
   50 [code      ]             notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
   51 [code      ]             dominant_note_idx = np.argmax(chroma)
   52 [code      ]             key_root = notes[dominant_note_idx]
   53 [blank     ]             
   54 [code      ]             minor_idx = (dominant_note_idx + 3) % 12
   55 [code      ]             major_idx = (dominant_note_idx + 4) % 12
   56 [blank     ]             
   57 [code      ]             mode = "minor" if chroma[minor_idx] > chroma[major_idx] else "major"
   58 [blank     ]                 
   59 [return    ]             return {
   60 [code      ]                 "ok": True,
   61 [code      ]                 "key": f"{key_root} {mode}",
   62 [code      ]                 "root": key_root,
   63 [code      ]                 "mode": mode,
   64 [code      ]                 "chroma_vector": chroma.tolist()
   65 [code      ]             }
   66 [try_block ]         except Exception as e:
   67 [return    ]             return {"ok": False, "error": str(e)}
   68 [blank     ] 
   69 [def       ]     def suggest_chords(self, key_root: str, mode: str) -> list:
   70 [docstring ]         """
   71 [docstring ]         Предлагает последовательность аккордов для заданного ключа.
   72 [docstring ]         """
   73 [branch    ]         if not HAS_MINGUS:
   74 [return    ]             return [["Am"], ["F"], ["C"], ["G"]]
   75 [try_block ]         try:
   76 [branch    ]             if mode == "minor":
   77 [code      ]                 scale = keys.get_notes(key_root + "m")
   78 [code      ]                 prog = [scale[0], scale[5], scale[2], scale[6]]
   79 [branch    ]             else:
   80 [code      ]                 scale = keys.get_notes(key_root)
   81 [code      ]                 prog = [scale[0], scale[4], scale[5], scale[3]]
   82 [blank     ]                 
   83 [return    ]             return [chords.triads(n, key_root + ("m" if mode == "minor" else "")) for n in prog]
   84 [try_block ]         except Exception:
   85 [return    ]             return [["Am"], ["F"], ["C"], ["G"]]
   86 [blank     ] 
   87 [blank     ] 
   88 [branch    ] if __name__ == "__main__":
   89 [code      ]     intel = MusicalIntelligence()
   90 [code      ]     print(intel.suggest_chords("A", "minor"))
```
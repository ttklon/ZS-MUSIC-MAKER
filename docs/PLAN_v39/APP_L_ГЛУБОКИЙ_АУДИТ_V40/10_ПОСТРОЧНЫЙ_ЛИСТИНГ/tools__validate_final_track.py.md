# ПОСТРОЧНЫЙ ЛИСТИНГ: `tools/validate_final_track.py`

**Всего строк:** 65

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 24 | 36.9 |
| blank | 14 | 21.5 |
| docstring | 8 | 12.3 |
| import | 5 | 7.7 |
| branch | 5 | 7.7 |
| return | 4 | 6.2 |
| def | 2 | 3.1 |
| try_block | 2 | 3.1 |
| raise | 1 | 1.5 |

## Полный листинг с классификацией
```
    1 [docstring ] """ZS Music Maker — финальная проверка качества трека.
    2 [blank     ] 
    3 [docstring ] v33 FIX (P2, SESSION_LOG v31.11): раньше здесь был жёстко зашит чужой путь
    4 [docstring ] /home/ubuntu/ZS-MUSIC-MAKER/... — на любой другой машине инструмент всегда
    5 [docstring ] печатал FAIL. Теперь путь берётся из argv[1]; без аргумента — ищем последний
    6 [docstring ] masters/*.wav в output/; если и его нет — честный usage + exit 2.
    7 [blank     ] 
    8 [docstring ] Использование:
    9 [docstring ]     python tools/validate_final_track.py [путь/к/track.wav]
   10 [docstring ] """
   11 [blank     ] 
   12 [import    ] import sys
   13 [import    ] from pathlib import Path
   14 [blank     ] 
   15 [code      ] sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
   16 [blank     ] 
   17 [import    ] from tests.test_audio_quality import validate_audio_file
   18 [import    ] import soundfile as sf
   19 [import    ] import numpy as np
   20 [blank     ] 
   21 [code      ] ROOT = Path(__file__).resolve().parents[1]
   22 [blank     ] 
   23 [blank     ] 
   24 [def       ] def _find_latest_master() -> Path | None:
   25 [code      ]     masters = sorted(ROOT.glob("output/**/masters/*.wav"))
   26 [return    ]     return masters[-1] if masters else None
   27 [blank     ] 
   28 [blank     ] 
   29 [def       ] def main() -> int:
   30 [branch    ]     if len(sys.argv) > 1:
   31 [code      ]         track_path = Path(sys.argv[1])
   32 [branch    ]     else:
   33 [code      ]         found = _find_latest_master()
   34 [branch    ]         if not found:
   35 [code      ]             print("USAGE: python tools/validate_final_track.py <path/to/track.wav>")
   36 [code      ]             print("(мастера в output/**/masters/*.wav не найдены)")
   37 [return    ]             return 2
   38 [code      ]         track_path = found
   39 [blank     ] 
   40 [code      ]     print(f"--- Final Quality Audit for: {track_path} ---")
   41 [try_block ]     try:
   42 [branch    ]         if not track_path.exists():
   43 [raise     ]             raise FileNotFoundError(f"File not found: {track_path}")
   44 [code      ]         validate_audio_file(str(track_path))
   45 [code      ]         data, sr = sf.read(str(track_path))
   46 [code      ]         peak = float(np.max(np.abs(data)))
   47 [code      ]         rms = float(np.sqrt(np.mean(data**2)))
   48 [code      ]         duration = len(data) / sr
   49 [code      ]         channels = data.shape[1] if data.ndim > 1 else 1
   50 [blank     ] 
   51 [code      ]         print("STATUS: PASS ✅")
   52 [code      ]         print(f"Peak Level: {peak:.4f} (Target <= 1.0)")
   53 [code      ]         print(f"RMS Level: {rms:.4f}")
   54 [code      ]         print(f"Duration: {duration:.2f}s")
   55 [code      ]         print(f"Sample Rate: {sr}Hz")
   56 [code      ]         print(f"Channels: {channels}")
   57 [return    ]         return 0
   58 [try_block ]     except Exception as e:
   59 [code      ]         print("STATUS: FAIL ❌")
   60 [code      ]         print(f"Error: {e}")
   61 [return    ]         return 1
   62 [blank     ] 
   63 [blank     ] 
   64 [branch    ] if __name__ == "__main__":
   65 [code      ]     sys.exit(main())
```
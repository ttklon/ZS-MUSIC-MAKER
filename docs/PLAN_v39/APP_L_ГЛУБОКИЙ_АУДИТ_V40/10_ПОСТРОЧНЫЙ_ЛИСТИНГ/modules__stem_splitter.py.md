# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/stem_splitter.py`

**Всего строк:** 75

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 31 | 41.3 |
| blank | 10 | 13.3 |
| docstring | 7 | 9.3 |
| import | 6 | 8.0 |
| try_block | 6 | 8.0 |
| return | 5 | 6.7 |
| branch | 5 | 6.7 |
| loop | 3 | 4.0 |
| def | 2 | 2.7 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [2a] stem_splitter.py — Demucs v4 (анализ, не копирование)
    3 [docstring ] Разбирает референс на vocals / drums / bass / other.
    4 [docstring ] Используется ТОЛЬКО для АНАЛИЗА структуры, НЕ для прямого копирования.
    5 [docstring ] """
    6 [blank     ] 
    7 [import    ] import os
    8 [import    ] import subprocess
    9 [import    ] import sys
   10 [blank     ] 
   11 [code      ] OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "stems")
   12 [blank     ] 
   13 [blank     ] 
   14 [def       ] def split_stems(input_path: str, model: str = "htdemucs") -> dict:
   15 [docstring ]     """Возвращает пути к 4 стемам."""
   16 [code      ]     os.makedirs(OUTPUT_DIR, exist_ok=True)
   17 [try_block ]     try:
   18 [import    ]         import demucs.separate  # noqa
   19 [try_block ]     except ImportError:
   20 [return    ]         return {"error": "Demucs не установлен. pip install demucs"}
   21 [blank     ] 
   22 [code      ]     cmd = [
   23 [code      ]         sys.executable,
   24 [code      ]         "-m",
   25 [code      ]         "demucs.separate",
   26 [code      ]         "-n",
   27 [code      ]         model,
   28 [code      ]         "-o",
   29 [code      ]         OUTPUT_DIR,
   30 [code      ]         "--mp3",
   31 [code      ]         input_path,
   32 [code      ]     ]
   33 [try_block ]     try:
   34 [code      ]         subprocess.run(cmd, check=True)
   35 [try_block ]     except subprocess.CalledProcessError as e:
   36 [return    ]         return {"error": f"Demucs failed: {e}"}
   37 [blank     ] 
   38 [code      ]     base = os.path.splitext(os.path.basename(input_path))[0]
   39 [code      ]     stem_dir = os.path.join(OUTPUT_DIR, model, base)
   40 [code      ]     result = {}
   41 [loop      ]     for stem in ["vocals", "drums", "bass", "other"]:
   42 [loop      ]         for ext in ("mp3", "wav"):
   43 [code      ]             p = os.path.join(stem_dir, f"{stem}.{ext}")
   44 [branch    ]             if os.path.exists(p):
   45 [code      ]                 result[stem] = p
   46 [code      ]                 break
   47 [code      ]     result["note"] = (
   48 [code      ]         "Стемы используются только как АНАЛИТИЧЕСКАЯ ссылка. Прямое копирование отключено."
   49 [code      ]     )
   50 [return    ]     return result
   51 [blank     ] 
   52 [blank     ] 
   53 [def       ] def analyze_arrangement(stems: dict) -> dict:
   54 [docstring ]     """Анализирует плотность стемов -> подсказка для BeatConstructor."""
   55 [try_block ]     try:
   56 [import    ]         import librosa
   57 [import    ]         import numpy as np
   58 [try_block ]     except ImportError:
   59 [return    ]         return {"error": "librosa не установлен"}
   60 [code      ]     report = {}
   61 [loop      ]     for name in ["vocals", "drums", "bass", "other"]:
   62 [code      ]         p = stems.get(name)
   63 [branch    ]         if not p or not os.path.exists(p):
   64 [code      ]             continue
   65 [code      ]         y, sr = librosa.load(p, sr=22050, mono=True)
   66 [code      ]         rms = float(np.mean(librosa.feature.rms(y=y)))
   67 [code      ]         report[name] = {"energy": round(rms, 4), "present": rms > 0.005}
   68 [return    ]     return report
   69 [blank     ] 
   70 [blank     ] 
   71 [branch    ] if __name__ == "__main__":
   72 [branch    ]     if len(sys.argv) < 2:
   73 [code      ]         print("Usage: python stem_splitter.py <track.mp3>")
   74 [branch    ]     else:
   75 [code      ]         print(split_stems(sys.argv[1]))
```
# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/essentia_analyzer.py`

**Всего строк:** 172

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 74 | 43.0 |
| blank | 33 | 19.2 |
| docstring | 20 | 11.6 |
| import | 9 | 5.2 |
| try_block | 8 | 4.7 |
| branch | 8 | 4.7 |
| return | 7 | 4.1 |
| comment | 7 | 4.1 |
| def | 4 | 2.3 |
| loop | 1 | 0.6 |
| stmt | 1 | 0.6 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v10 — Essentia Analyzer
    3 [docstring ] =========================================
    4 [docstring ] Продвинутая музыковедческая аналитика (ТЗ 3.2).
    5 [blank     ] 
    6 [docstring ] Использует Essentia (если установлена) для извлечения:
    7 [docstring ]   - danceability, energy, valence
    8 [docstring ]   - loudness (integrated LUFS-приближение)
    9 [docstring ]   - key/scale/strength (более точно чем librosa)
   10 [docstring ]   - beats_confidence, onset_rate
   11 [docstring ]   - dynamic_complexity
   12 [docstring ]   - spectral_flux, HFC, dissonance
   13 [blank     ] 
   14 [docstring ] Если Essentia недоступна — graceful fallback на librosa-based
   15 [docstring ] расчёты (уже реализованы в modules/analyzer.py).
   16 [blank     ] 
   17 [docstring ] Автор: v10 «Chart Killer Pro»
   18 [docstring ] """
   19 [blank     ] 
   20 [import    ] from __future__ import annotations
   21 [blank     ] 
   22 [import    ] import json
   23 [import    ] import logging
   24 [import    ] from pathlib import Path
   25 [import    ] from typing import Any
   26 [blank     ] 
   27 [code      ] log = logging.getLogger("zsmm.essentia")
   28 [blank     ] 
   29 [try_block ] try:
   30 [import    ]     import essentia.standard as es  # type: ignore
   31 [blank     ] 
   32 [code      ]     ESSENTIA_OK = True
   33 [try_block ] except Exception:
   34 [code      ]     ESSENTIA_OK = False
   35 [code      ]     log.warning("Essentia не найдена — используем librosa fallback")
   36 [blank     ] 
   37 [try_block ] try:
   38 [import    ]     import librosa
   39 [import    ]     import numpy as np
   40 [try_block ] except Exception:
   41 [code      ]     librosa = None
   42 [code      ]     np = None
   43 [blank     ] 
   44 [blank     ] 
   45 [def       ] def analyze_advanced(audio_path: str, sr: int = 44100) -> dict[str, Any]:
   46 [docstring ]     """
   47 [docstring ]     Возвращает расширенный музыковедческий отчёт.
   48 [blank     ] 
   49 [docstring ]     Никогда не бросает исключение — всегда возвращает dict.
   50 [docstring ]     Если ничего не удалось, возвращает {"ok": False, "reason": ...}.
   51 [docstring ]     """
   52 [code      ]     p = Path(audio_path)
   53 [branch    ]     if not p.exists():
   54 [return    ]         return {"ok": False, "reason": f"file not found: {audio_path}"}
   55 [blank     ] 
   56 [branch    ]     if ESSENTIA_OK:
   57 [try_block ]         try:
   58 [return    ]             return _analyze_essentia(str(p), sr)
   59 [try_block ]         except Exception as e:
   60 [code      ]             log.warning("Essentia сбой, fallback librosa: %s", e)
   61 [blank     ] 
   62 [return    ]     return _analyze_librosa_fallback(str(p), sr)
   63 [blank     ] 
   64 [blank     ] 
   65 [def       ] def _analyze_essentia(audio_path: str, sr: int) -> dict[str, Any]:
   66 [code      ]     loader = es.MonoLoader(filename=audio_path, sampleRate=sr)
   67 [code      ]     audio = loader()
   68 [blank     ] 
   69 [comment   ]     # Rhythm
   70 [code      ]     rhythm = es.RhythmExtractor2013(method="multifeature")
   71 [code      ]     bpm, beats, beats_conf, _, beats_intervals = rhythm(audio)
   72 [blank     ] 
   73 [comment   ]     # Key
   74 [code      ]     key_ex = es.KeyExtractor()
   75 [code      ]     key, scale, key_str = key_ex(audio)
   76 [blank     ] 
   77 [comment   ]     # Danceability
   78 [code      ]     danceability, _ = es.Danceability()(audio)
   79 [blank     ] 
   80 [comment   ]     # Loudness (LUFS approximation via ReplayGain proxy)
   81 [code      ]     loudness = es.ReplayGain()(audio)
   82 [blank     ] 
   83 [comment   ]     # Dynamic complexity
   84 [code      ]     dyn_cmp, dyn_loud = es.DynamicComplexity()(audio)
   85 [blank     ] 
   86 [comment   ]     # Spectral
   87 [code      ]     hfc = float(
   88 [code      ]         np.mean(
   89 [code      ]             [
   90 [code      ]                 es.HFC()(es.Spectrum()(es.Windowing()(fr)))
   91 [loop      ]                 for fr in es.FrameGenerator(audio, 2048, 1024)
   92 [code      ]             ]
   93 [code      ]         )
   94 [code      ]     )
   95 [blank     ] 
   96 [code      ]     onset = es.OnsetRate()
   97 [code      ]     onsets, onset_rate = onset(audio)
   98 [blank     ] 
   99 [return    ]     return {
  100 [code      ]         "ok": True,
  101 [code      ]         "engine": "essentia",
  102 [code      ]         "bpm": float(bpm),
  103 [code      ]         "beats_confidence": float(beats_conf),
  104 [code      ]         "key": key,
  105 [code      ]         "scale": scale,
  106 [code      ]         "key_strength": float(key_str),
  107 [code      ]         "danceability": float(danceability),
  108 [code      ]         "loudness_replaygain_db": float(loudness),
  109 [code      ]         "dynamic_complexity": float(dyn_cmp),
  110 [code      ]         "hfc": hfc,
  111 [code      ]         "onset_rate": float(onset_rate),
  112 [code      ]         "n_beats": len(beats),
  113 [code      ]     }
  114 [blank     ] 
  115 [blank     ] 
  116 [def       ] def _analyze_librosa_fallback(audio_path: str, sr: int) -> dict[str, Any]:
  117 [branch    ]     if librosa is None:
  118 [return    ]         return {"ok": False, "reason": "no librosa & no essentia"}
  119 [try_block ]     try:
  120 [code      ]         y, sr = librosa.load(audio_path, sr=sr, mono=True)
  121 [code      ]         tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
  122 [code      ]         onset_env = librosa.onset.onset_strength(y=y, sr=sr)
  123 [code      ]         onset_rate = float(np.mean(onset_env))
  124 [code      ]         rms = float(np.mean(librosa.feature.rms(y=y)))
  125 [code      ]         centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
  126 [code      ]         flatness = float(np.mean(librosa.feature.spectral_flatness(y=y)))
  127 [code      ]         chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
  128 [code      ]         key_idx = int(np.argmax(np.mean(chroma, axis=1)))
  129 [code      ]         keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
  130 [blank     ] 
  131 [comment   ]         # Простая эвристика danceability = функция от tempo стабильности и RMS
  132 [code      ]         beat_stability = 1.0
  133 [branch    ]         if len(beats) > 2:
  134 [code      ]             intervals = np.diff(librosa.frames_to_time(beats, sr=sr))
  135 [code      ]             beat_stability = 1.0 / (1.0 + float(np.std(intervals)))
  136 [code      ]         danceability = min(1.0, beat_stability * (0.3 + min(rms * 5, 0.7)))
  137 [blank     ] 
  138 [return    ]         return {
  139 [code      ]             "ok": True,
  140 [code      ]             "engine": "librosa_fallback",
  141 [code      ]             "bpm": float(tempo),
  142 [code      ]             "key": keys[key_idx],
  143 [code      ]             "scale": (
  144 [code      ]                 "major"
  145 [branch    ]                 if np.mean(chroma[[0, 4, 7]]) > np.mean(chroma[[0, 3, 7]])
  146 [code      ]                 else "minor"
  147 [code      ]             ),
  148 [code      ]             "danceability": float(danceability),
  149 [code      ]             "rms": rms,
  150 [code      ]             "spectral_centroid": centroid,
  151 [code      ]             "spectral_flatness": flatness,
  152 [code      ]             "onset_rate": onset_rate,
  153 [code      ]             "n_beats": len(beats),
  154 [code      ]         }
  155 [try_block ]     except Exception as e:
  156 [return    ]         return {"ok": False, "reason": str(e)}
  157 [blank     ] 
  158 [blank     ] 
  159 [def       ] def save_report(report: dict[str, Any], out_json: str) -> None:
  160 [code      ]     Path(out_json).parent.mkdir(parents=True, exist_ok=True)
  161 [stmt      ]     with open(out_json, "w", encoding="utf-8") as f:
  162 [code      ]         json.dump(report, f, ensure_ascii=False, indent=2)
  163 [blank     ] 
  164 [blank     ] 
  165 [branch    ] if __name__ == "__main__":
  166 [import    ]     import sys
  167 [blank     ] 
  168 [branch    ]     if len(sys.argv) < 2:
  169 [code      ]         print(json.dumps({"engine_available": ESSENTIA_OK}, ensure_ascii=False))
  170 [branch    ]     else:
  171 [code      ]         rep = analyze_advanced(sys.argv[1])
  172 [code      ]         print(json.dumps(rep, ensure_ascii=False, indent=2))
```
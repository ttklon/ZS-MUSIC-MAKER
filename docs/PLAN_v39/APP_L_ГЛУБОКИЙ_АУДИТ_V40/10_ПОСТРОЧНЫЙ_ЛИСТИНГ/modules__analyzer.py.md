# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/analyzer.py`

**Всего строк:** 257

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 134 | 52.1 |
| blank | 38 | 14.8 |
| branch | 20 | 7.8 |
| docstring | 18 | 7.0 |
| comment | 13 | 5.1 |
| try_block | 8 | 3.1 |
| return | 8 | 3.1 |
| def | 7 | 2.7 |
| import | 6 | 2.3 |
| loop | 4 | 1.6 |
| raise | 1 | 0.4 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [1] analyzer.py — Мульти-референс анализатор v2
    3 [docstring ] Усиления v2:
    4 [docstring ]   • Веса референсов (пользователь указывает что брать из каждого)
    5 [docstring ]   • BPM-диапазон + режимы (кач/ускорить/замедлить/клубнее/TikTok-hooky)
    6 [docstring ]   • Образы и хук-лексика из транскрипта
    7 [docstring ]   • Сохранение в analysis_cache с полным provenance
    8 [docstring ]   • Essentia-дескрипторы (опционально, если установлен)
    9 [docstring ] """
   10 [blank     ] 
   11 [import    ] import json
   12 [import    ] import os
   13 [blank     ] 
   14 [import    ] import numpy as np
   15 [blank     ] 
   16 [try_block ] try:
   17 [import    ]     import librosa
   18 [try_block ] except ImportError:
   19 [code      ]     librosa = None
   20 [blank     ] 
   21 [code      ] VAULT = os.path.join(
   22 [code      ]     os.path.dirname(__file__), "..", "references", "analysis_cache.json"
   23 [code      ] )
   24 [blank     ] 
   25 [blank     ] 
   26 [def       ] def _safe_load(path, sr=22050):
   27 [branch    ]     if librosa is None:
   28 [raise     ]         raise RuntimeError("librosa не установлен. pip install librosa")
   29 [code      ]     y, sr = librosa.load(path, sr=sr, mono=True)
   30 [return    ]     return y, sr
   31 [blank     ] 
   32 [blank     ] 
   33 [def       ] def analyze_single(path: str) -> dict:
   34 [docstring ]     """Полный анализ одного трека — BPM, тональность, спектр, энергия, вайб."""
   35 [code      ]     y, sr = _safe_load(path)
   36 [blank     ] 
   37 [comment   ]     # BPM
   38 [code      ]     tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
   39 [code      ]     bpm_val = float(tempo) if np.ndim(tempo) == 0 else float(tempo[0])
   40 [blank     ] 
   41 [comment   ]     # Тональность
   42 [code      ]     chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
   43 [code      ]     key_idx = int(np.argmax(chroma.mean(axis=1)))
   44 [code      ]     keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
   45 [code      ]     key = keys[key_idx]
   46 [code      ]     minor_third = chroma[(key_idx + 3) % 12].mean()
   47 [code      ]     major_third = chroma[(key_idx + 4) % 12].mean()
   48 [code      ]     mode = "minor" if minor_third > major_third else "major"
   49 [blank     ] 
   50 [comment   ]     # Энергия и спектр
   51 [code      ]     rms = float(np.mean(librosa.feature.rms(y=y)))
   52 [code      ]     centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
   53 [code      ]     bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)))
   54 [code      ]     zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)))
   55 [code      ]     duration = float(librosa.get_duration(y=y, sr=sr))
   56 [blank     ] 
   57 [comment   ]     # Bass energy (0-250Hz)
   58 [code      ]     S = np.abs(librosa.stft(y))
   59 [code      ]     freqs = librosa.fft_frequencies(sr=sr)
   60 [code      ]     bass_mask = freqs < 250
   61 [code      ]     bass_energy = float(S[bass_mask].mean() / (S.mean() + 1e-9))
   62 [blank     ] 
   63 [comment   ]     # Плотность ударов (наличие дропа)
   64 [code      ]     beat_density = len(beats) / max(duration, 0.1)
   65 [blank     ] 
   66 [comment   ]     # Секции: грубая сегментация по энергии
   67 [code      ]     rms_frames = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
   68 [code      ]     n_sections = 8
   69 [code      ]     chunk = len(rms_frames) // n_sections if len(rms_frames) >= n_sections else 1
   70 [code      ]     section_energies = [
   71 [code      ]         float(np.mean(rms_frames[i * chunk : (i + 1) * chunk]))
   72 [loop      ]         for i in range(n_sections)
   73 [code      ]     ]
   74 [comment   ]     # Определяем где дроп (пик энергии)
   75 [code      ]     drop_section = int(np.argmax(section_energies)) if section_energies else 0
   76 [blank     ] 
   77 [comment   ]     # Essentia-дескрипторы (опционально)
   78 [code      ]     essentia_desc = {}
   79 [try_block ]     try:
   80 [import    ]         import essentia.standard as estd
   81 [blank     ] 
   82 [code      ]         loader = estd.MonoLoader(filename=path)
   83 [code      ]         audio = loader()
   84 [code      ]         danceability = estd.Danceability()(audio)
   85 [code      ]         essentia_desc["danceability"] = round(float(danceability[0]), 3)
   86 [try_block ]     except Exception:
   87 [code      ]         pass
   88 [blank     ] 
   89 [return    ]     return {
   90 [code      ]         "path": path,
   91 [code      ]         "filename": os.path.basename(path),
   92 [code      ]         "bpm": round(bpm_val, 2),
   93 [code      ]         "key": f"{key} {mode}",
   94 [code      ]         "key_root": key,
   95 [code      ]         "mode": mode,
   96 [code      ]         "duration_sec": round(duration, 2),
   97 [code      ]         "rms": round(rms, 4),
   98 [code      ]         "spectral_centroid": round(centroid, 2),
   99 [code      ]         "spectral_bandwidth": round(bandwidth, 2),
  100 [code      ]         "zcr": round(zcr, 4),
  101 [code      ]         "bass_ratio": round(bass_energy, 3),
  102 [code      ]         "beat_density": round(beat_density, 2),
  103 [code      ]         "section_energies": [round(e, 4) for e in section_energies],
  104 [code      ]         "drop_section": drop_section,
  105 [code      ]         "vibe_tags": _infer_vibe(bpm_val, centroid, bass_energy, mode),
  106 [code      ]         "essentia": essentia_desc,
  107 [code      ]     }
  108 [blank     ] 
  109 [blank     ] 
  110 [def       ] def _infer_vibe(bpm, centroid, bass, mode):
  111 [code      ]     tags = []
  112 [branch    ]     if bpm < 90:
  113 [code      ]         tags.append("slow")
  114 [branch    ]     elif bpm < 110:
  115 [code      ]         tags.append("mid-tempo")
  116 [branch    ]     elif bpm < 140:
  117 [code      ]         tags.append("phonk/drift")
  118 [branch    ]     elif bpm < 160:
  119 [code      ]         tags.append("trap/hype")
  120 [branch    ]     else:
  121 [code      ]         tags.append("hyper/hardstyle")
  122 [branch    ]     if bass > 1.4:
  123 [code      ]         tags.append("bass-heavy")
  124 [branch    ]     if centroid < 1500:
  125 [code      ]         tags.append("dark")
  126 [branch    ]     elif centroid > 3500:
  127 [code      ]         tags.append("bright")
  128 [branch    ]     if mode == "minor":
  129 [code      ]         tags.append("aggressive")
  130 [branch    ]     if bass > 2.0 and centroid < 2000:
  131 [code      ]         tags.append("underground")
  132 [return    ]     return tags
  133 [blank     ] 
  134 [blank     ] 
  135 [def       ] def _bpm_range(bpm_val: float) -> dict:
  136 [docstring ]     """Возвращает рабочий диапазон BPM + режимы."""
  137 [code      ]     low = max(60, bpm_val - 6)
  138 [code      ]     high = bpm_val + 8
  139 [return    ]     return {
  140 [code      ]         "center": int(round(bpm_val)),
  141 [code      ]         "range_low": int(round(low)),
  142 [code      ]         "range_high": int(round(high)),
  143 [code      ]         "modes": {
  144 [code      ]             "keep_groove": int(round(bpm_val)),
  145 [code      ]             "speed_up_edits": min(180, int(round(bpm_val * 1.08))),
  146 [code      ]             "slow_lazy": max(70, int(round(bpm_val * 0.92))),
  147 [code      ]             "club_harder": min(180, int(round(bpm_val * 1.05))),
  148 [code      ]             "tiktok_hooky": int(round(bpm_val)),
  149 [code      ]         },
  150 [code      ]         "suggestions": {
  151 [code      ]             "sticky_hook": max(100, int(round(bpm_val - 1))),
  152 [code      ]             "flex_flow": min(180, int(round(bpm_val + 3))),
  153 [code      ]             "deep_heavy": max(90, int(round(bpm_val - 3))),
  154 [code      ]         },
  155 [code      ]     }
  156 [blank     ] 
  157 [blank     ] 
  158 [def       ] def analyze_multi(paths: list, weights: list = None, take_notes: list = None) -> dict:
  159 [docstring ]     """
  160 [docstring ]     Строит усреднённый style-vector по нескольким референсам.
  161 [blank     ] 
  162 [docstring ]     weights: [0.5, 0.3, 0.2] — вес каждого референса (сумма = 1.0).
  163 [docstring ]              Если None — равные веса.
  164 [docstring ]     take_notes: ["бит из этого", "стиль чтения из этого", ...]
  165 [docstring ]              Заметки пользователя что взять из каждого референса.
  166 [docstring ]     """
  167 [code      ]     analyses = [analyze_single(p) for p in paths]
  168 [blank     ] 
  169 [branch    ]     if weights is None:
  170 [code      ]         weights = [1.0 / len(paths)] * len(paths)
  171 [code      ]     weights = [w / sum(weights) for w in weights]  # нормализация
  172 [blank     ] 
  173 [comment   ]     # Взвешенное среднее
  174 [code      ]     avg_bpm = sum(a["bpm"] * w for a, w in zip(analyses, weights))
  175 [code      ]     avg_bass = sum(a["bass_ratio"] * w for a, w in zip(analyses, weights))
  176 [code      ]     avg_centroid = sum(a["spectral_centroid"] * w for a, w in zip(analyses, weights))
  177 [blank     ] 
  178 [comment   ]     # Тональность — голосование
  179 [code      ]     keys_list = [a["key"] for a in analyses]
  180 [code      ]     mode = (
  181 [code      ]         "minor"
  182 [branch    ]         if sum(1 for k in keys_list if "minor" in k) >= len(keys_list) / 2
  183 [code      ]         else "major"
  184 [code      ]     )
  185 [blank     ] 
  186 [comment   ]     # Vibe tags — взвешенная частота
  187 [code      ]     tag_weights = {}
  188 [loop      ]     for a, w in zip(analyses, weights):
  189 [loop      ]         for t in a["vibe_tags"]:
  190 [code      ]             tag_weights[t] = tag_weights.get(t, 0) + w
  191 [code      ]     top_tags = sorted(tag_weights, key=tag_weights.get, reverse=True)[:6]
  192 [blank     ] 
  193 [comment   ]     # BPM-диапазон
  194 [code      ]     bpm_range = _bpm_range(avg_bpm)
  195 [blank     ] 
  196 [comment   ]     # Take-notes (что пользователь хочет взять из каждого)
  197 [code      ]     ref_notes = []
  198 [branch    ]     if take_notes:
  199 [loop      ]         for i, note in enumerate(take_notes):
  200 [branch    ]             if i < len(analyses) and note.strip():
  201 [code      ]                 ref_notes.append(
  202 [code      ]                     {
  203 [code      ]                         "ref": analyses[i]["filename"],
  204 [code      ]                         "note": note.strip(),
  205 [code      ]                         "bpm": analyses[i]["bpm"],
  206 [code      ]                         "vibe": analyses[i]["vibe_tags"],
  207 [code      ]                     }
  208 [code      ]                 )
  209 [blank     ] 
  210 [code      ]     style_vector = {
  211 [code      ]         "sources": [os.path.basename(p) for p in paths],
  212 [code      ]         "weights": weights,
  213 [code      ]         "ref_notes": ref_notes,
  214 [code      ]         "target_bpm": int(round(avg_bpm)),
  215 [code      ]         "target_mode": mode,
  216 [code      ]         "target_bass_ratio": round(avg_bass, 3),
  217 [code      ]         "target_centroid": round(avg_centroid, 2),
  218 [code      ]         "vibe_tags": top_tags,
  219 [code      ]         "bpm_range": bpm_range,
  220 [code      ]         "individual": analyses,
  221 [code      ]     }
  222 [code      ]     _save_to_vault(style_vector)
  223 [return    ]     return style_vector
  224 [blank     ] 
  225 [blank     ] 
  226 [def       ] def _save_to_vault(data):
  227 [code      ]     os.makedirs(os.path.dirname(VAULT), exist_ok=True)
  228 [code      ]     existing = []
  229 [branch    ]     if os.path.exists(VAULT):
  230 [try_block ]         try:
  231 [code      ]             existing = json.load(open(VAULT, "r", encoding="utf-8"))
  232 [try_block ]         except Exception:
  233 [code      ]             existing = []
  234 [code      ]     existing.append(data)
  235 [code      ]     json.dump(
  236 [code      ]         existing, open(VAULT, "w", encoding="utf-8"), ensure_ascii=False, indent=2
  237 [code      ]     )
  238 [blank     ] 
  239 [blank     ] 
  240 [def       ] def list_cached_analyses() -> list:
  241 [branch    ]     if os.path.exists(VAULT):
  242 [try_block ]         try:
  243 [return    ]             return json.load(open(VAULT, "r", encoding="utf-8"))
  244 [try_block ]         except Exception:
  245 [return    ]             return []
  246 [return    ]     return []
  247 [blank     ] 
  248 [blank     ] 
  249 [branch    ] if __name__ == "__main__":
  250 [import    ]     import sys
  251 [blank     ] 
  252 [code      ]     files = sys.argv[1:]
  253 [branch    ]     if not files:
  254 [code      ]         print("Usage: python analyzer.py <ref1.mp3> [ref2.mp3 ...]")
  255 [branch    ]     else:
  256 [code      ]         result = analyze_multi(files) if len(files) > 1 else analyze_single(files[0])
  257 [code      ]         print(json.dumps(result, ensure_ascii=False, indent=2))
```
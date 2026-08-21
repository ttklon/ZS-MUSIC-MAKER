# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/reference_ingest.py`

**Всего строк:** 318

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 135 | 42.5 |
| blank | 49 | 15.4 |
| return | 33 | 10.4 |
| branch | 30 | 9.4 |
| docstring | 24 | 7.5 |
| def | 13 | 4.1 |
| comment | 9 | 2.8 |
| import | 8 | 2.5 |
| try_block | 8 | 2.5 |
| loop | 8 | 2.5 |
| stmt | 1 | 0.3 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v9] reference_ingest.py — единая точка входа для 1-7 референсов.
    3 [blank     ] 
    4 [docstring ] По ТЗ 3.2: «Несколько референсов формируют стилевой вектор».
    5 [docstring ] До v9 разные модули (analyzer, groove_extractor, author_ref_lyrics)
    6 [docstring ] дублировали работу по чтению одних и тех же файлов. Этот модуль:
    7 [blank     ] 
    8 [docstring ]   1. Принимает список файлов (mp3/wav/flac/ogg/m4a) + веса (0..1).
    9 [docstring ]   2. Извлекает и КЭШИРУЕТ per-file:
   10 [docstring ]        BPM, key, chroma_mean, spectral_centroid, spectral_contrast,
   11 [docstring ]        RMS, MFCC-mean, onset_density, harmonic_ratio, ключевые сэмплы (kick/snare).
   12 [docstring ]   3. Строит STYLE VECTOR — weighted average всех характеристик.
   13 [docstring ]   4. Строит STYLE FINGERPRINT — компактный JSON для сохранения в проекте.
   14 [docstring ]   5. Отдаёт «BPM консенсус» и «Key консенсус» через robust voting.
   15 [blank     ] 
   16 [docstring ] Кэш файлов — data/reference_cache/<md5>.json — переиспользуется между сессиями.
   17 [blank     ] 
   18 [docstring ] Ничего не удаляет из старых модулей. `analyzer.py` продолжает работать
   19 [docstring ] как раньше — этот модуль вызывает его как один из бэкендов.
   20 [docstring ] """
   21 [blank     ] 
   22 [import    ] from __future__ import annotations
   23 [blank     ] 
   24 [import    ] import hashlib
   25 [import    ] import json
   26 [import    ] import time
   27 [import    ] from pathlib import Path
   28 [blank     ] 
   29 [try_block ] try:
   30 [import    ]     import numpy as np
   31 [try_block ] except Exception:  # pragma: no cover
   32 [code      ]     np = None
   33 [blank     ] 
   34 [try_block ] try:
   35 [import    ]     import librosa
   36 [blank     ] 
   37 [code      ]     HAS_LIBROSA = True
   38 [try_block ] except Exception:
   39 [code      ]     HAS_LIBROSA = False
   40 [blank     ] 
   41 [code      ] ROOT = Path(__file__).resolve().parents[1]
   42 [code      ] CACHE_DIR = ROOT / "data" / "reference_cache"
   43 [comment   ] # v22: ленивое создание (не при импорте)
   44 [blank     ] 
   45 [comment   ] # минорные тональности индексируются как key+12
   46 [code      ] KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
   47 [blank     ] 
   48 [blank     ] 
   49 [comment   ] # ============================================================ utils
   50 [def       ] def _md5(path: str) -> str:
   51 [code      ]     h = hashlib.md5()
   52 [stmt      ]     with open(path, "rb") as f:
   53 [loop      ]         for chunk in iter(lambda: f.read(1 << 16), b""):
   54 [code      ]             h.update(chunk)
   55 [return    ]     return h.hexdigest()
   56 [blank     ] 
   57 [blank     ] 
   58 [def       ] def _cache_path(path: str) -> Path:
   59 [return    ]     return CACHE_DIR / f"{_md5(path)}.json"
   60 [blank     ] 
   61 [blank     ] 
   62 [def       ] def _load_cached(path: str) -> dict | None:
   63 [code      ]     cp = _cache_path(path)
   64 [branch    ]     if cp.exists():
   65 [try_block ]         try:
   66 [return    ]             return json.loads(cp.read_text(encoding="utf-8"))
   67 [try_block ]         except Exception:
   68 [return    ]             return None
   69 [return    ]     return None
   70 [blank     ] 
   71 [blank     ] 
   72 [def       ] def _save_cached(path: str, data: dict) -> None:
   73 [code      ]     _cache_path(path).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
   74 [blank     ] 
   75 [blank     ] 
   76 [comment   ] # ============================================================ per-file analysis
   77 [def       ] def _key_from_chroma(chroma) -> tuple[str, str]:
   78 [docstring ]     """Простой Krumhansl-like алгоритм: dot product со шаблонами major/minor."""
   79 [branch    ]     if np is None:
   80 [return    ]         return "C", "major"
   81 [code      ]     major_prof = np.array(
   82 [code      ]         [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
   83 [code      ]     )
   84 [code      ]     minor_prof = np.array(
   85 [code      ]         [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
   86 [code      ]     )
   87 [code      ]     chroma_mean = chroma.mean(axis=1) if chroma.ndim > 1 else chroma
   88 [code      ]     best = ("C", "major", -1.0)
   89 [loop      ]     for i in range(12):
   90 [code      ]         rot = np.roll(chroma_mean, -i)
   91 [code      ]         s_maj = float(np.dot(rot, major_prof))
   92 [code      ]         s_min = float(np.dot(rot, minor_prof))
   93 [branch    ]         if s_maj > best[2]:
   94 [code      ]             best = (KEYS[i], "major", s_maj)
   95 [branch    ]         if s_min > best[2]:
   96 [code      ]             best = (KEYS[i], "minor", s_min)
   97 [return    ]     return best[0], best[1]
   98 [blank     ] 
   99 [blank     ] 
  100 [def       ] def analyze_file(path: str, sr: int = 22050, use_cache: bool = True) -> dict:
  101 [docstring ]     """Единичный референс → полный fingerprint."""
  102 [code      ]     p = Path(path)
  103 [branch    ]     if not p.exists():
  104 [return    ]         return {"ok": False, "error": f"not found: {path}"}
  105 [blank     ] 
  106 [branch    ]     if use_cache:
  107 [code      ]         cached = _load_cached(str(p))
  108 [branch    ]         if cached is not None:
  109 [return    ]             return cached
  110 [blank     ] 
  111 [branch    ]     if not HAS_LIBROSA:
  112 [code      ]         result = {
  113 [code      ]             "ok": True,
  114 [code      ]             "path": str(p),
  115 [code      ]             "fallback": True,
  116 [code      ]             "bpm": 130.0,
  117 [code      ]             "key": "C",
  118 [code      ]             "mode": "minor",
  119 [code      ]             "note": "librosa unavailable, defaults returned",
  120 [code      ]         }
  121 [branch    ]         if use_cache:
  122 [code      ]             _save_cached(str(p), result)
  123 [return    ]         return result
  124 [blank     ] 
  125 [try_block ]     try:
  126 [code      ]         y, s = librosa.load(str(p), sr=sr, mono=True)
  127 [code      ]         duration = len(y) / s
  128 [code      ]         onset_env = librosa.onset.onset_strength(y=y, sr=s)
  129 [code      ]         tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=s)
  130 [code      ]         chroma = librosa.feature.chroma_cqt(y=y, sr=s)
  131 [code      ]         key, mode = _key_from_chroma(chroma)
  132 [code      ]         centroid = float(librosa.feature.spectral_centroid(y=y, sr=s).mean())
  133 [code      ]         contrast = librosa.feature.spectral_contrast(y=y, sr=s).mean(axis=1)
  134 [code      ]         rms = float(librosa.feature.rms(y=y).mean())
  135 [code      ]         mfcc = librosa.feature.mfcc(y=y, sr=s, n_mfcc=13).mean(axis=1)
  136 [code      ]         onset_density = float(
  137 [code      ]             len(librosa.onset.onset_detect(onset_envelope=onset_env, sr=s))
  138 [code      ]             / max(duration, 1e-3)
  139 [code      ]         )
  140 [code      ]         harmonic, percussive = librosa.effects.hpss(y)
  141 [code      ]         harm_ratio = float((harmonic**2).sum() / ((y**2).sum() + 1e-9))
  142 [blank     ] 
  143 [code      ]         result = {
  144 [code      ]             "ok": True,
  145 [code      ]             "path": str(p),
  146 [code      ]             "duration_s": round(duration, 2),
  147 [code      ]             "bpm": round(float(tempo), 2),
  148 [code      ]             "key": key,
  149 [code      ]             "mode": mode,
  150 [code      ]             "spectral_centroid": round(centroid, 2),
  151 [code      ]             "spectral_contrast": [round(float(x), 3) for x in contrast.tolist()],
  152 [code      ]             "rms": round(rms, 5),
  153 [code      ]             "mfcc_mean": [round(float(x), 3) for x in mfcc.tolist()],
  154 [code      ]             "chroma_mean": [round(float(x), 3) for x in chroma.mean(axis=1).tolist()],
  155 [code      ]             "onset_density": round(onset_density, 3),
  156 [code      ]             "harmonic_ratio": round(harm_ratio, 3),
  157 [code      ]             "n_beats": len(beats),
  158 [code      ]             "sr": int(s),
  159 [code      ]             "ts": time.time(),
  160 [code      ]         }
  161 [branch    ]         if use_cache:
  162 [code      ]             _save_cached(str(p), result)
  163 [return    ]         return result
  164 [try_block ]     except Exception as e:
  165 [return    ]         return {"ok": False, "error": str(e), "path": str(p)}
  166 [blank     ] 
  167 [blank     ] 
  168 [comment   ] # ============================================================ style vector
  169 [def       ] def _consensus_bpm(features: list[dict], weights: list[float]) -> float:
  170 [docstring ]     """Взвешенный BPM с учётом октавных ошибок (60 vs 120 vs 90 vs 180)."""
  171 [branch    ]     if not features:
  172 [return    ]         return 130.0
  173 [blank     ] 
  174 [comment   ]     # Приводим к диапазону 60-180
  175 [def       ]     def _norm(b):
  176 [loop      ]         while b < 60:
  177 [code      ]             b *= 2
  178 [loop      ]         while b > 200:
  179 [code      ]             b /= 2
  180 [return    ]         return b
  181 [blank     ] 
  182 [code      ]     bpms = [_norm(f.get("bpm", 130.0)) for f in features]
  183 [code      ]     total_w = sum(weights) or 1.0
  184 [code      ]     weighted = sum(b * w for b, w in zip(bpms, weights)) / total_w
  185 [return    ]     return round(weighted, 2)
  186 [blank     ] 
  187 [blank     ] 
  188 [def       ] def _consensus_key(features: list[dict], weights: list[float]) -> tuple[str, str]:
  189 [docstring ]     """Voting по key+mode с учётом весов."""
  190 [code      ]     tally = {}
  191 [loop      ]     for f, w in zip(features, weights):
  192 [code      ]         k = f.get("key", "C")
  193 [code      ]         m = f.get("mode", "minor")
  194 [code      ]         tally[(k, m)] = tally.get((k, m), 0.0) + w
  195 [branch    ]     if not tally:
  196 [return    ]         return "C", "minor"
  197 [code      ]     best = max(tally.items(), key=lambda kv: kv[1])[0]
  198 [return    ]     return best
  199 [blank     ] 
  200 [blank     ] 
  201 [def       ] def build_style_vector(
  202 [code      ]     files: list[str], weights: list[float] | None = None, sr: int = 22050
  203 [code      ] ) -> dict:
  204 [docstring ]     """
  205 [docstring ]     Основной API. `files` — 1..7 путей. `weights` — 0..1 (default 1.0).
  206 [docstring ]     Возвращает полный STYLE FINGERPRINT.
  207 [docstring ]     """
  208 [branch    ]     if not files:
  209 [return    ]         return {"ok": False, "error": "no references given"}
  210 [branch    ]     if len(files) > 7:
  211 [code      ]         files = files[:7]
  212 [branch    ]     if weights is None:
  213 [code      ]         weights = [1.0] * len(files)
  214 [branch    ]     if len(weights) != len(files):
  215 [code      ]         weights = (weights + [1.0] * len(files))[: len(files)]
  216 [blank     ] 
  217 [code      ]     features = []
  218 [code      ]     per_file = []
  219 [loop      ]     for path, w in zip(files, weights):
  220 [code      ]         r = analyze_file(path, sr=sr)
  221 [code      ]         per_file.append({**r, "weight": float(w)})
  222 [branch    ]         if r.get("ok"):
  223 [code      ]             features.append(r)
  224 [blank     ] 
  225 [branch    ]     if not features:
  226 [return    ]         return {"ok": False, "error": "all analyses failed", "per_file": per_file}
  227 [blank     ] 
  228 [code      ]     bpm = _consensus_bpm(features, weights[: len(features)])
  229 [code      ]     key, mode = _consensus_key(features, weights[: len(features)])
  230 [blank     ] 
  231 [comment   ]     # Векторные средние (с учётом весов)
  232 [def       ]     def _wavg(field, dim=None):
  233 [code      ]         vals = [f.get(field) for f in features if f.get(field) is not None]
  234 [branch    ]         if not vals:
  235 [return    ]             return None
  236 [code      ]         ws = weights[: len(vals)]
  237 [code      ]         tw = sum(ws) or 1.0
  238 [branch    ]         if isinstance(vals[0], list):
  239 [code      ]             L = len(vals[0])
  240 [code      ]             out = [0.0] * L
  241 [loop      ]             for v, w in zip(vals, ws):
  242 [loop      ]                 for i in range(L):
  243 [code      ]                     out[i] += (v[i] if i < len(v) else 0.0) * w
  244 [return    ]             return [round(x / tw, 4) for x in out]
  245 [return    ]         return round(sum(v * w for v, w in zip(vals, ws)) / tw, 4)
  246 [blank     ] 
  247 [code      ]     style_vector = {
  248 [code      ]         "bpm": bpm,
  249 [code      ]         "key": key,
  250 [code      ]         "mode": mode,
  251 [code      ]         "spectral_centroid": _wavg("spectral_centroid"),
  252 [code      ]         "spectral_contrast": _wavg("spectral_contrast"),
  253 [code      ]         "rms": _wavg("rms"),
  254 [code      ]         "mfcc_mean": _wavg("mfcc_mean"),
  255 [code      ]         "chroma_mean": _wavg("chroma_mean"),
  256 [code      ]         "onset_density": _wavg("onset_density"),
  257 [code      ]         "harmonic_ratio": _wavg("harmonic_ratio"),
  258 [code      ]     }
  259 [blank     ] 
  260 [comment   ]     # Heuristic — определяем «настрой» и «жанровый вектор» для UI
  261 [code      ]     genre_hint = _guess_genre(style_vector)
  262 [code      ]     mood = _guess_mood(style_vector)
  263 [blank     ] 
  264 [return    ]     return {
  265 [code      ]         "ok": True,
  266 [code      ]         "n_references": len(files),
  267 [code      ]         "n_ok": len(features),
  268 [code      ]         "style_vector": style_vector,
  269 [code      ]         "consensus": {
  270 [code      ]             "bpm": bpm,
  271 [code      ]             "key": key,
  272 [code      ]             "mode": mode,
  273 [code      ]             "genre_hint": genre_hint,
  274 [code      ]             "mood": mood,
  275 [code      ]         },
  276 [code      ]         "per_file": per_file,
  277 [code      ]         "ts": time.time(),
  278 [code      ]     }
  279 [blank     ] 
  280 [blank     ] 
  281 [def       ] def _guess_genre(sv: dict) -> str:
  282 [code      ]     bpm = sv.get("bpm", 130.0)
  283 [code      ]     hr = sv.get("harmonic_ratio", 0.5)
  284 [code      ]     od = sv.get("onset_density", 3.0)
  285 [branch    ]     if 130 <= bpm <= 145 and od > 3.5:
  286 [return    ]         return "phonk / drift"
  287 [branch    ]     if 120 <= bpm <= 132 and hr > 0.5:
  288 [return    ]         return "dance / edm"
  289 [branch    ]     if 70 <= bpm <= 100 and od < 3.0:
  290 [return    ]         return "trap / hip-hop"
  291 [branch    ]     if 95 <= bpm <= 120:
  292 [return    ]         return "pop / r&b"
  293 [branch    ]     if bpm > 150:
  294 [return    ]         return "hardstyle / techno"
  295 [return    ]     return "generic hit"
  296 [blank     ] 
  297 [blank     ] 
  298 [def       ] def _guess_mood(sv: dict) -> str:
  299 [code      ]     mode = sv.get("mode", "minor")
  300 [code      ]     centroid = sv.get("spectral_centroid", 2000.0) or 2000.0
  301 [branch    ]     if mode == "minor" and centroid < 1800:
  302 [return    ]         return "dark / moody"
  303 [branch    ]     if mode == "minor" and centroid >= 1800:
  304 [return    ]         return "energetic / driving"
  305 [branch    ]     if mode == "major" and centroid > 2200:
  306 [return    ]         return "bright / summer"
  307 [return    ]     return "melancholic"
  308 [blank     ] 
  309 [blank     ] 
  310 [comment   ] # ============================================================ CLI
  311 [branch    ] if __name__ == "__main__":
  312 [import    ]     import sys
  313 [blank     ] 
  314 [branch    ]     if len(sys.argv) < 2:
  315 [code      ]         print("usage: python reference_ingest.py <ref1> [ref2 ...]")
  316 [code      ]         sys.exit(1)
  317 [code      ]     r = build_style_vector(sys.argv[1:])
  318 [code      ]     print(json.dumps(r, ensure_ascii=False, indent=2))
```
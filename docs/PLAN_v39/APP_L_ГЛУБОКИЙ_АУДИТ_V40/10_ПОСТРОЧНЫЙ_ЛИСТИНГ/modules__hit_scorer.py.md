# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/hit_scorer.py`

**Всего строк:** 588

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 266 | 45.2 |
| branch | 69 | 11.7 |
| blank | 62 | 10.5 |
| return | 53 | 9.0 |
| docstring | 50 | 8.5 |
| try_block | 30 | 5.1 |
| comment | 23 | 3.9 |
| def | 19 | 3.2 |
| import | 10 | 1.7 |
| loop | 5 | 0.9 |
| raise | 1 | 0.2 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v9] hit_scorer.py — HIT POTENTIAL SCORER.
    3 [blank     ] 
    4 [docstring ] Оценивает «хитовость» финального master.wav по 12 метрикам, скоррелированным
    5 [docstring ] с реальными чартовыми характеристиками (Spotify Viral 50 / TikTok Sounds /
    6 [docstring ] Apple Music Top 100). Идеологически — расширение auto_qa, но фокус смещён с
    7 [docstring ] «живости звука» на «шансы попасть в чарт / зайти на TikTok».
    8 [blank     ] 
    9 [docstring ] Метрики (0..100 каждая, weighted sum → HitScore 0..100):
   10 [docstring ]   1. hook_energy          — пик громкости в припеве vs куплете
   11 [docstring ]   2. hook_repeatability   — сколько раз повторяется главный мотив
   12 [docstring ]   3. chorus_catchiness    — гармоническая яркость + ритмическая простота припева
   13 [docstring ]   4. drop_impact          — контраст drop/build (bass energy delta)
   14 [docstring ]   5. tiktok_hookability   — есть ли 15-30 сек «вирусный кусок» с моментальным входом
   15 [docstring ]   6. bpm_dance_fitness    — BPM в диапазоне 120-140 (dance) или 70-95 (trap)
   16 [docstring ]   7. loudness_lufs        — интегральный LUFS близко к -8..-10 (стриминг-мастер)
   17 [docstring ]   8. stereo_width         — стерео-разъезд (correlation < 0.85)
   18 [docstring ]   9. low_end_power        — sub-bass (20-80 Hz) не рыхлый
   19 [docstring ]  10. vocal_presence       — вокал в диапазоне 2-5 kHz читается
   20 [docstring ]  11. structure_clarity    — узнаваемые границы intro/verse/chorus/outro
   21 [docstring ]  12. novelty              — не «формульный» — уникальные звуковые события
   22 [blank     ] 
   23 [docstring ] Возвращает:
   24 [docstring ]   {
   25 [docstring ]     "hit_score": float 0..100,
   26 [docstring ]     "verdict":   "chart_ready" | "solid" | "needs_work" | "flop_risk",
   27 [docstring ]     "metrics":   {name: {"score": float, "raw": Any, "hint": str}},
   28 [docstring ]     "tiktok_slice": {"start_sec": float, "end_sec": float, "reason": str},
   29 [docstring ]     "actions":     [str, ...]  # что доработать
   30 [docstring ]   }
   31 [blank     ] 
   32 [docstring ] Без внешних сервисов. librosa/numpy — единственные зависимости.
   33 [docstring ] Graceful fallback при отсутствии librosa: только LUFS-подобная оценка через soundfile.
   34 [docstring ] """
   35 [blank     ] 
   36 [import    ] from __future__ import annotations
   37 [blank     ] 
   38 [import    ] import json
   39 [import    ] import math
   40 [import    ] import time
   41 [import    ] from pathlib import Path
   42 [blank     ] 
   43 [comment   ] # ---------- граcеful imports ----------
   44 [try_block ] try:
   45 [import    ]     import numpy as np
   46 [try_block ] except Exception:  # pragma: no cover
   47 [code      ]     np = None
   48 [blank     ] 
   49 [try_block ] try:
   50 [import    ]     import librosa
   51 [code      ]     HAS_LIBROSA = True
   52 [try_block ] except Exception:
   53 [code      ]     HAS_LIBROSA = False
   54 [blank     ] 
   55 [try_block ] try:
   56 [import    ]     import soundfile as sf
   57 [code      ]     HAS_SF = True
   58 [try_block ] except Exception:
   59 [code      ]     HAS_SF = False
   60 [blank     ] 
   61 [try_block ] try:
   62 [import    ]     import pyloudnorm as pyln
   63 [code      ]     HAS_PYLOUDNORM = True
   64 [try_block ] except ImportError:
   65 [code      ]     HAS_PYLOUDNORM = False
   66 [blank     ] 
   67 [blank     ] 
   68 [comment   ] # ============================================================ utils
   69 [def       ] def _load_audio(path: str, sr: int = 22050):
   70 [docstring ]     """Возвращает (y, sr). Использует librosa если есть, иначе soundfile+resample naive."""
   71 [branch    ]     if HAS_LIBROSA:
   72 [code      ]         y, s = librosa.load(path, sr=sr, mono=True)
   73 [return    ]         return y, s
   74 [branch    ]     if HAS_SF:
   75 [code      ]         y, s = sf.read(path, always_2d=False)
   76 [branch    ]         if hasattr(y, "ndim") and y.ndim > 1:
   77 [code      ]             y = y.mean(axis=1)
   78 [return    ]         return y, s
   79 [raise     ]     raise RuntimeError("Neither librosa nor soundfile available")
   80 [blank     ] 
   81 [blank     ] 
   82 [def       ] def _rms(y) -> float:
   83 [branch    ]     if np is None or y is None or len(y) == 0:
   84 [return    ]         return 0.0
   85 [return    ]     return float(np.sqrt(np.mean(np.square(y)) + 1e-12))
   86 [blank     ] 
   87 [blank     ] 
   88 [def       ] def _db(x: float) -> float:
   89 [return    ]     return float(20.0 * math.log10(max(x, 1e-9)))
   90 [blank     ] 
   91 [blank     ] 
   92 [comment   ] # ============================================================ metrics
   93 [def       ] def _hook_energy(y, sr) -> tuple[float, float]:
   94 [docstring ]     """Ищем сегмент с максимальной локальной громкостью — это предполагаемый припев."""
   95 [branch    ]     if np is None or len(y) < sr * 8:
   96 [return    ]         return 50.0, _rms(y)
   97 [code      ]     win = int(sr * 4)
   98 [code      ]     hop = int(sr * 1)
   99 [code      ]     rms_curve = []
  100 [loop      ]     for i in range(0, len(y) - win, hop):
  101 [code      ]         rms_curve.append(_rms(y[i : i + win]))
  102 [branch    ]     if not rms_curve:
  103 [return    ]         return 50.0, 0.0
  104 [code      ]     peak = max(rms_curve)
  105 [code      ]     median = sorted(rms_curve)[len(rms_curve) // 2]
  106 [code      ]     ratio = peak / max(median, 1e-6)
  107 [comment   ]     # Хит-припев обычно на +30-60% громче медианы
  108 [code      ]     score = min(100.0, max(0.0, (ratio - 1.0) * 200.0))
  109 [return    ]     return score, ratio
  110 [blank     ] 
  111 [blank     ] 
  112 [def       ] def _hook_repeatability(y, sr) -> tuple[float, int]:
  113 [docstring ]     """Повторяемость главного мотива.
  114 [blank     ] 
  115 [docstring ]     v26 FIX (P1): короткие треки (<20 с) раньше всегда получали 55.0/0
  116 [docstring ]     (ложный нейтрал) и не теряли баллы, но не давали сигнала к улучшению.
  117 [docstring ]     Теперь считаем AC RMS-огибающей даже без librosa — честный signal.
  118 [docstring ]     """
  119 [branch    ]     if not HAS_LIBROSA or len(y) < sr * 20:
  120 [branch    ]         if np is None or len(y) < sr * 2:
  121 [return    ]             return 55.0, 0
  122 [try_block ]         try:
  123 [code      ]             win = int(sr * 0.5)
  124 [code      ]             hop = int(sr * 0.25)
  125 [code      ]             rms_curve = np.array(
  126 [code      ]                 [_rms(y[i : i + win]) for i in range(0, len(y) - win, hop)],
  127 [code      ]                 dtype="float32",
  128 [code      ]             )
  129 [branch    ]             if len(rms_curve) < 8:
  130 [return    ]                 return 55.0, 0
  131 [code      ]             rms_curve = rms_curve - rms_curve.mean()
  132 [code      ]             _norm = float(np.sum(rms_curve * rms_curve)) + 1e-9
  133 [code      ]             _peaks = 0
  134 [loop      ]             for lag in range(4, min(len(rms_curve) - 1, 32)):
  135 [code      ]                 ac = float(np.sum(rms_curve[:-lag] * rms_curve[lag:])) / _norm
  136 [branch    ]                 if ac > 0.5:
  137 [code      ]                     _peaks += 1
  138 [code      ]             score = min(100.0, 40.0 + _peaks * 6.0)
  139 [return    ]             return score, _peaks
  140 [try_block ]         except Exception:
  141 [return    ]             return 55.0, 0
  142 [try_block ]     try:
  143 [code      ]         chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=1024)
  144 [code      ]         ssm = np.dot(chroma.T, chroma)
  145 [code      ]         ssm /= (
  146 [code      ]             np.linalg.norm(chroma, axis=0)[:, None]
  147 [code      ]             * np.linalg.norm(chroma, axis=0)[None, :]
  148 [code      ]             + 1e-9
  149 [code      ]         )
  150 [code      ]         off = int(20 * sr / 1024)
  151 [branch    ]         if off >= ssm.shape[0]:
  152 [code      ]             off = int(4 * sr / 1024)
  153 [branch    ]             if off >= ssm.shape[0] - 1 or off < 1:
  154 [return    ]                 return 50.0, 0
  155 [code      ]         diag = np.diagonal(ssm, offset=off)
  156 [code      ]         repeats = int((diag > 0.85).sum())
  157 [code      ]         score = min(100.0, repeats * 8.0 + 30.0)
  158 [return    ]         return score, repeats
  159 [try_block ]     except Exception:
  160 [return    ]         return 50.0, 0
  161 [blank     ] 
  162 [blank     ] 
  163 [def       ] def _chorus_catchiness(y, sr) -> tuple[float, dict]:
  164 [docstring ]     """Комбинация: гармоническая простота (мажор/минор readable) + ритмическая регулярность."""
  165 [branch    ]     if not HAS_LIBROSA:
  166 [return    ]         return 55.0, {}
  167 [try_block ]     try:
  168 [code      ]         onset_env = librosa.onset.onset_strength(y=y, sr=sr)
  169 [code      ]         tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
  170 [comment   ]         # Регулярность: sharpness пиков огибающей
  171 [code      ]         peaks = librosa.util.peak_pick(
  172 [code      ]             onset_env, pre_max=3, post_max=3, pre_avg=5, post_avg=5, delta=0.5, wait=10
  173 [code      ]         )
  174 [code      ]         regularity = min(100.0, len(peaks) * 0.6 + 40.0)
  175 [comment   ]         # Гармоническая простота — chroma variance (низкая = простая гармония)
  176 [code      ]         chroma = librosa.feature.chroma_stft(y=y, sr=sr)
  177 [code      ]         chroma_var = float(np.mean(np.var(chroma, axis=1)))
  178 [code      ]         harmonic_simplicity = max(0.0, min(100.0, 100.0 - chroma_var * 400.0))
  179 [code      ]         score = 0.6 * regularity + 0.4 * harmonic_simplicity
  180 [return    ]         return score, {
  181 [code      ]             "tempo": float(tempo),
  182 [code      ]             "peaks": len(peaks),
  183 [code      ]             "chroma_var": chroma_var,
  184 [code      ]         }
  185 [try_block ]     except Exception:
  186 [return    ]         return 55.0, {}
  187 [blank     ] 
  188 [blank     ] 
  189 [def       ] def _drop_impact(y, sr) -> tuple[float, float]:
  190 [docstring ]     """Ищем самый резкий скачок RMS — drop. Хит-drop даёт +6..+9 dB."""
  191 [branch    ]     if np is None or len(y) < sr * 8:
  192 [return    ]         return 50.0, 0.0
  193 [code      ]     win = int(sr * 2)
  194 [code      ]     hop = int(sr * 0.5)
  195 [code      ]     rms_curve = np.array([_rms(y[i : i + win]) for i in range(0, len(y) - win, hop)])
  196 [branch    ]     if len(rms_curve) < 4:
  197 [return    ]         return 50.0, 0.0
  198 [code      ]     diff = np.diff(rms_curve)
  199 [code      ]     max_jump = float(diff.max())
  200 [code      ]     baseline = float(np.median(np.abs(diff)))
  201 [code      ]     ratio = max_jump / max(baseline, 1e-6)
  202 [code      ]     score = min(100.0, ratio * 12.0)
  203 [return    ]     return score, ratio
  204 [blank     ] 
  205 [blank     ] 
  206 [def       ] def _tiktok_hookability(y, sr) -> tuple[float, dict]:
  207 [docstring ]     """Находит 15-30 сек кусок с моментальным входом (energy>median в первые 2 сек)."""
  208 [branch    ]     if np is None or len(y) < sr * 15:
  209 [return    ]         return 40.0, {"start_sec": 0.0, "end_sec": 15.0, "reason": "трек короткий"}
  210 [code      ]     win_len = int(sr * 25)  # 25 sec — sweet spot TikTok
  211 [code      ]     hop = int(sr * 2)
  212 [code      ]     best = {"score": 0.0, "start": 0}
  213 [code      ]     global_med = _rms(y)
  214 [loop      ]     for i in range(0, len(y) - win_len, hop):
  215 [code      ]         seg = y[i : i + win_len]
  216 [code      ]         head_rms = _rms(seg[: int(sr * 2)])
  217 [code      ]         overall = _rms(seg)
  218 [comment   ]         # Хороший TikTok-slice: сразу громко + держит уровень
  219 [branch    ]         if head_rms > global_med * 0.9 and overall > global_med:
  220 [code      ]             score = (head_rms / max(global_med, 1e-6)) * 30.0 + (
  221 [code      ]                 overall / max(global_med, 1e-6)
  222 [code      ]             ) * 20.0
  223 [branch    ]             if score > best["score"]:
  224 [code      ]                 best["score"] = score
  225 [code      ]                 best["start"] = i
  226 [branch    ]     if best["score"] == 0.0:
  227 [comment   ]         # fallback: самый громкий 25-сек кусок
  228 [code      ]         rms_c = [_rms(y[i : i + win_len]) for i in range(0, len(y) - win_len, hop)]
  229 [code      ]         idx = int(np.argmax(rms_c)) if rms_c else 0
  230 [code      ]         best["start"] = idx * hop
  231 [code      ]         best["score"] = 45.0
  232 [code      ]     start_sec = best["start"] / sr
  233 [return    ]     return min(100.0, best["score"] + 20.0), {
  234 [code      ]         "start_sec": round(start_sec, 2),
  235 [code      ]         "end_sec": round(start_sec + 25.0, 2),
  236 [code      ]         "reason": "immediate hook + sustained energy",
  237 [code      ]     }
  238 [blank     ] 
  239 [blank     ] 
  240 [def       ] def _bpm_dance_fitness(y, sr) -> tuple[float, float]:
  241 [branch    ]     if not HAS_LIBROSA:
  242 [return    ]         return 60.0, 0.0
  243 [try_block ]     try:
  244 [code      ]         tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
  245 [code      ]         t = float(tempo)
  246 [comment   ]         # Sweet spots
  247 [code      ]         best_ranges = [(120, 140, 100), (70, 95, 90), (95, 120, 75), (140, 160, 80)]
  248 [code      ]         score = 40.0
  249 [loop      ]         for lo, hi, s in best_ranges:
  250 [branch    ]             if lo <= t <= hi:
  251 [code      ]                 score = float(s)
  252 [code      ]                 break
  253 [return    ]         return score, t
  254 [try_block ]     except Exception:
  255 [return    ]         return 60.0, 0.0
  256 [blank     ] 
  257 [blank     ] 
  258 [def       ] def _loudness_lufs(y, sr) -> tuple[float, float]:
  259 [docstring ]     """Интегральная громкость. Использует pyloudnorm (BS.1770) если есть, иначе RMS-fallback.
  260 [blank     ]     
  261 [docstring ]     v26 FIX (P1): librosa грузит mono-downmix (L+R)/2 — теряет ~3 dB RMS
  262 [docstring ]     относительно стерео dBFS. Sweet-spot сдвинут на -3 dB.
  263 [docstring ]     """
  264 [branch    ]     if np is None:
  265 [return    ]         return 60.0, -14.0
  266 [blank     ]         
  267 [branch    ]     if HAS_PYLOUDNORM:
  268 [try_block ]         try:
  269 [comment   ]             # y is mono from _load_audio
  270 [code      ]             meter = pyln.Meter(sr)
  271 [code      ]             lufs = float(meter.integrated_loudness(y))
  272 [comment   ]             # Для LUFS таргет обычно -14..-9
  273 [branch    ]             if -14.0 <= lufs <= -9.0:
  274 [code      ]                 score = 98.0
  275 [branch    ]             elif -16.0 <= lufs < -14.0:
  276 [code      ]                 score = 80.0
  277 [branch    ]             elif -9.0 < lufs <= -7.0:
  278 [code      ]                 score = 85.0
  279 [branch    ]             else:
  280 [code      ]                 score = 50.0
  281 [return    ]             return score, lufs
  282 [try_block ]         except Exception:
  283 [code      ]             pass
  284 [blank     ] 
  285 [comment   ]     # Fallback to RMS-based pseudo-LUFS
  286 [code      ]     rms = _rms(y)
  287 [code      ]     dbfs = _db(rms)
  288 [branch    ]     if -14.0 <= dbfs <= -10.0:
  289 [code      ]         score = 95.0
  290 [branch    ]     elif -17.0 <= dbfs < -14.0:
  291 [code      ]         score = 75.0
  292 [branch    ]     elif -10.0 < dbfs <= -7.0:
  293 [code      ]         score = 80.0
  294 [branch    ]     elif -7.0 < dbfs <= -4.0:
  295 [code      ]         score = 60.0
  296 [branch    ]     else:
  297 [code      ]         score = 40.0
  298 [return    ]     return score, dbfs
  299 [blank     ] 
  300 [blank     ] 
  301 [def       ] def _stereo_width(path: str) -> tuple[float, float]:
  302 [docstring ]     """Требуется стерео-файл. Считает корреляцию каналов."""
  303 [branch    ]     if not HAS_SF or np is None:
  304 [return    ]         return 60.0, 1.0
  305 [try_block ]     try:
  306 [code      ]         y, _ = sf.read(path, always_2d=True)
  307 [branch    ]         if y.shape[1] < 2:
  308 [return    ]             return 30.0, 1.0
  309 [code      ]         l, r = y[:, 0], y[:, 1]
  310 [code      ]         corr = float(np.corrcoef(l, r)[0, 1])
  311 [comment   ]         # width = 1 - corr; хиты обычно 0.15..0.4 → corr 0.6..0.85
  312 [branch    ]         if 0.55 <= corr <= 0.85:
  313 [code      ]             score = 90.0
  314 [branch    ]         elif corr < 0.55:
  315 [code      ]             score = 70.0  # слишком широко
  316 [branch    ]         elif corr < 0.95:
  317 [code      ]             score = 65.0
  318 [branch    ]         else:
  319 [code      ]             score = 40.0  # почти моно
  320 [return    ]         return score, corr
  321 [try_block ]     except Exception:
  322 [return    ]         return 60.0, 1.0
  323 [blank     ] 
  324 [blank     ] 
  325 [def       ] def _low_end_power(y, sr) -> tuple[float, float]:
  326 [branch    ]     if not HAS_LIBROSA:
  327 [return    ]         return 60.0, 0.0
  328 [try_block ]     try:
  329 [code      ]         S = np.abs(librosa.stft(y, n_fft=2048))
  330 [code      ]         freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
  331 [code      ]         low_mask = (freqs >= 20) & (freqs <= 80)
  332 [code      ]         mid_mask = (freqs >= 200) & (freqs <= 2000)
  333 [code      ]         low_energy = float(S[low_mask, :].mean())
  334 [code      ]         mid_energy = float(S[mid_mask, :].mean())
  335 [code      ]         ratio = low_energy / max(mid_energy, 1e-9)
  336 [comment   ]         # Хиты dance/trap: low/mid ≈ 0.6..1.2
  337 [branch    ]         if 0.55 <= ratio <= 1.3:
  338 [code      ]             score = 92.0
  339 [branch    ]         elif 0.3 <= ratio < 0.55:
  340 [code      ]             score = 68.0
  341 [branch    ]         elif ratio > 1.3:
  342 [code      ]             score = 70.0
  343 [branch    ]         else:
  344 [code      ]             score = 45.0
  345 [return    ]         return score, ratio
  346 [try_block ]     except Exception:
  347 [return    ]         return 60.0, 0.0
  348 [blank     ] 
  349 [blank     ] 
  350 [def       ] def _vocal_presence(y, sr) -> tuple[float, float]:
  351 [branch    ]     if not HAS_LIBROSA:
  352 [return    ]         return 60.0, 0.0
  353 [try_block ]     try:
  354 [code      ]         S = np.abs(librosa.stft(y, n_fft=2048))
  355 [code      ]         freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
  356 [code      ]         voc_mask = (freqs >= 2000) & (freqs <= 5000)
  357 [code      ]         all_energy = float(S.mean())
  358 [code      ]         voc_energy = float(S[voc_mask, :].mean())
  359 [code      ]         ratio = voc_energy / max(all_energy, 1e-9)
  360 [code      ]         score = min(100.0, ratio * 90.0 + 25.0)
  361 [return    ]         return score, ratio
  362 [try_block ]     except Exception:
  363 [return    ]         return 60.0, 0.0
  364 [blank     ] 
  365 [blank     ] 
  366 [def       ] def _structure_clarity(y, sr) -> tuple[float, int]:
  367 [branch    ]     if not HAS_LIBROSA or len(y) < sr * 30:
  368 [return    ]         return 55.0, 0
  369 [try_block ]     try:
  370 [comment   ]         # segmentation по chroma+mfcc через spectral clustering — простая версия
  371 [code      ]         rms = librosa.feature.rms(y=y, hop_length=1024)[0]
  372 [comment   ]         # normalize
  373 [code      ]         rms = (rms - rms.mean()) / (rms.std() + 1e-9)
  374 [comment   ]         # найдём точки сильного изменения
  375 [code      ]         changes = np.where(np.abs(np.diff(rms)) > 1.2)[0]
  376 [comment   ]         # ожидаем 3-6 крупных секций
  377 [code      ]         n = len(changes)
  378 [branch    ]         if 3 <= n <= 8:
  379 [code      ]             score = 90.0
  380 [branch    ]         elif n < 3:
  381 [code      ]             score = 50.0
  382 [branch    ]         else:
  383 [code      ]             score = 70.0
  384 [return    ]         return score, n
  385 [try_block ]     except Exception:
  386 [return    ]         return 55.0, 0
  387 [blank     ] 
  388 [blank     ] 
  389 [def       ] def _novelty(y, sr) -> tuple[float, float]:
  390 [docstring ]     """Насколько трек «неформульный» — вариативность спектра во времени."""
  391 [branch    ]     if not HAS_LIBROSA:
  392 [return    ]         return 60.0, 0.0
  393 [try_block ]     try:
  394 [code      ]         S = np.abs(librosa.stft(y, n_fft=2048))
  395 [code      ]         col_var = float(np.mean(np.var(S, axis=1)))
  396 [code      ]         row_var = float(np.mean(np.var(S, axis=0)))
  397 [comment   ]         # v26: Используем и col_var (время), и row_var (частоты)
  398 [code      ]         combined_var = (col_var + row_var * 0.1) / 1.1
  399 [code      ]         score = min(100.0, combined_var * 8e5 + 40.0) if combined_var > 0 else 40.0
  400 [return    ]         return score, combined_var
  401 [try_block ]     except Exception:
  402 [return    ]         return 60.0, 0.0
  403 [blank     ] 
  404 [blank     ] 
  405 [comment   ] # ============================================================ verdict
  406 [code      ] WEIGHTS = {
  407 [code      ]     "hook_energy": 1.5,
  408 [code      ]     "hook_repeatability": 1.3,
  409 [code      ]     "chorus_catchiness": 1.4,
  410 [code      ]     "drop_impact": 1.2,
  411 [code      ]     "tiktok_hookability": 1.5,
  412 [code      ]     "bpm_dance_fitness": 0.8,
  413 [code      ]     "loudness_lufs": 1.0,
  414 [code      ]     "stereo_width": 0.7,
  415 [code      ]     "low_end_power": 1.0,
  416 [code      ]     "vocal_presence": 1.1,
  417 [code      ]     "structure_clarity": 1.0,
  418 [code      ]     "novelty": 0.8,
  419 [code      ] }
  420 [blank     ] 
  421 [blank     ] 
  422 [def       ] def _verdict(score: float) -> str:
  423 [branch    ]     if score >= 82.0:
  424 [return    ]         return "chart_ready"
  425 [branch    ]     if score >= 68.0:
  426 [return    ]         return "solid"
  427 [branch    ]     if score >= 50.0:
  428 [return    ]         return "needs_work"
  429 [return    ]     return "flop_risk"
  430 [blank     ] 
  431 [blank     ] 
  432 [def       ] def _actions(metrics: dict) -> list[str]:
  433 [code      ]     out = []
  434 [loop      ]     for name, m in metrics.items():
  435 [code      ]         s = m.get("score", 0.0)
  436 [branch    ]         if s >= 65.0:
  437 [code      ]             continue
  438 [branch    ]         if name == "hook_energy":
  439 [code      ]             out.append(
  440 [code      ]                 "Припев тише куплета — подними RMS припева на +2 dB "
  441 [code      ]                 "или сделай drop громче"
  442 [code      ]             )
  443 [branch    ]         elif name == "hook_repeatability":
  444 [code      ]             out.append("Повторяй главный мотив ≥3 раза (chorus/hook loop)")
  445 [branch    ]         elif name == "chorus_catchiness":
  446 [code      ]             out.append(
  447 [code      ]                 "Упрости гармонию припева до 2-3 аккордов, ритм — " "равномерные 4/4"
  448 [code      ]             )
  449 [branch    ]         elif name == "drop_impact":
  450 [code      ]             out.append(
  451 [code      ]                 "Добавь build-up (риз) перед drop и полусекунду тишины "
  452 [code      ]                 "перед first-beat drop"
  453 [code      ]             )
  454 [branch    ]         elif name == "tiktok_hookability":
  455 [code      ]             out.append(
  456 [code      ]                 "Сделай моментальный вход в первые 2 сек (без длинного "
  457 [code      ]                 "intro) — для TikTok/Reels"
  458 [code      ]             )
  459 [branch    ]         elif name == "bpm_dance_fitness":
  460 [code      ]             out.append(
  461 [code      ]                 "BPM вне dance-диапазонов. Целься в 120-140 "
  462 [code      ]                 "(dance/phonk) или 70-95 (trap)"
  463 [code      ]             )
  464 [branch    ]         elif name == "loudness_lufs":
  465 [code      ]             out.append(
  466 [code      ]                 "LUFS вне streaming-target. Смастеринг под -9 dBFS "
  467 [code      ]                 "интегрированной громкости"
  468 [code      ]             )
  469 [branch    ]         elif name == "stereo_width":
  470 [code      ]             out.append(
  471 [code      ]                 "Стерео-картинка слишком узкая или слишком широкая. "
  472 [code      ]                 "Целься в correlation 0.6-0.85"
  473 [code      ]             )
  474 [branch    ]         elif name == "low_end_power":
  475 [code      ]             out.append("Проработай sub-bass 20-80 Hz — добавь 808 или " "sub-sine")
  476 [branch    ]         elif name == "vocal_presence":
  477 [code      ]             out.append(
  478 [code      ]                 "Вокал не читается в 2-5 kHz. Подними presence-полку " "+2 dB на 3 kHz"
  479 [code      ]             )
  480 [branch    ]         elif name == "structure_clarity":
  481 [code      ]             out.append(
  482 [code      ]                 "Секции слишком похожи. Добавь контраст между "
  483 [code      ]                 "куплетом и припевом (плотность, элементы)"
  484 [code      ]             )
  485 [branch    ]         elif name == "novelty":
  486 [code      ]             out.append(
  487 [code      ]                 "Трек звучит формульно. Добавь уникальный саунд-дизайн "
  488 [code      ]                 "элемент (FX, стоп, воб, риверс)"
  489 [code      ]             )
  490 [return    ]     return out
  491 [blank     ] 
  492 [blank     ] 
  493 [comment   ] # ============================================================ main API
  494 [def       ] def score_track(master_wav: str, out_json: str | None = None, sr: int = 22050) -> dict:
  495 [docstring ]     """
  496 [docstring ]     Основной API. `master_wav` — путь к финальному мастеру.
  497 [docstring ]     Возвращает полный отчёт. Если out_json — сохраняет.
  498 [docstring ]     """
  499 [code      ]     t0 = time.time()
  500 [code      ]     p = Path(master_wav)
  501 [branch    ]     if not p.exists():
  502 [return    ]         return {
  503 [code      ]             "error": f"file not found: {master_wav}",
  504 [code      ]             "hit_score": 0.0,
  505 [code      ]             "verdict": "flop_risk",
  506 [code      ]         }
  507 [blank     ] 
  508 [try_block ]     try:
  509 [code      ]         y, s = _load_audio(str(p), sr=sr)
  510 [try_block ]     except Exception as e:
  511 [return    ]         return {"error": f"load failed: {e}", "hit_score": 0.0, "verdict": "flop_risk"}
  512 [blank     ] 
  513 [code      ]     metrics = {}
  514 [blank     ] 
  515 [def       ]     def _add(name, val_tuple, hint=""):
  516 [code      ]         score, raw = val_tuple if isinstance(val_tuple, tuple) else (val_tuple, None)
  517 [code      ]         metrics[name] = {"score": round(float(score), 2), "raw": raw, "hint": hint}
  518 [blank     ] 
  519 [code      ]     _add(
  520 [code      ]         "hook_energy", _hook_energy(y, s), "loud-quiet dynamic between chorus and verse"
  521 [code      ]     )
  522 [code      ]     _add(
  523 [code      ]         "hook_repeatability",
  524 [code      ]         _hook_repeatability(y, s),
  525 [code      ]         "how many times main motif repeats",
  526 [code      ]     )
  527 [code      ]     _add(
  528 [code      ]         "chorus_catchiness",
  529 [code      ]         _chorus_catchiness(y, s),
  530 [code      ]         "harmonic simplicity + rhythmic regularity",
  531 [code      ]     )
  532 [code      ]     _add("drop_impact", _drop_impact(y, s), "biggest RMS jump = drop")
  533 [code      ]     tt_score, tt_slice = _tiktok_hookability(y, s)
  534 [code      ]     _add(
  535 [code      ]         "tiktok_hookability",
  536 [code      ]         (tt_score, tt_slice),
  537 [code      ]         "instant-hook 25 sec slice for TikTok",
  538 [code      ]     )
  539 [code      ]     _add("bpm_dance_fitness", _bpm_dance_fitness(y, s), "BPM in dance/trap sweet spot")
  540 [code      ]     _add(
  541 [code      ]         "loudness_lufs", _loudness_lufs(y, s), "integrated dBFS ≈ LUFS streaming target"
  542 [code      ]     )
  543 [code      ]     _add("stereo_width", _stereo_width(str(p)), "channel correlation 0.6-0.85")
  544 [code      ]     _add("low_end_power", _low_end_power(y, s), "20-80 Hz vs 200-2000 Hz ratio")
  545 [code      ]     _add("vocal_presence", _vocal_presence(y, s), "2-5 kHz vocal readability")
  546 [code      ]     _add(
  547 [code      ]         "structure_clarity",
  548 [code      ]         _structure_clarity(y, s),
  549 [code      ]         "distinct intro/verse/chorus/outro",
  550 [code      ]     )
  551 [code      ]     _add("novelty", _novelty(y, s), "non-formulaic spectral variety")
  552 [blank     ] 
  553 [comment   ]     # weighted total
  554 [code      ]     total_w = sum(WEIGHTS.values())
  555 [code      ]     hit_score = sum(metrics[k]["score"] * WEIGHTS[k] for k in WEIGHTS) / total_w
  556 [blank     ] 
  557 [code      ]     report = {
  558 [code      ]         "hit_score": round(hit_score, 2),
  559 [code      ]         "verdict": _verdict(hit_score),
  560 [code      ]         "metrics": metrics,
  561 [code      ]         "tiktok_slice": tt_slice,
  562 [code      ]         "actions": _actions(metrics),
  563 [code      ]         "meta": {
  564 [code      ]             "file": str(p),
  565 [code      ]             "duration_s": round(len(y) / s, 2),
  566 [code      ]             "sr": s,
  567 [code      ]             "elapsed_s": round(time.time() - t0, 2),
  568 [code      ]             "librosa": HAS_LIBROSA,
  569 [code      ]             "soundfile": HAS_SF,
  570 [code      ]         },
  571 [code      ]     }
  572 [blank     ] 
  573 [branch    ]     if out_json:
  574 [code      ]         Path(out_json).write_text(
  575 [code      ]             json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
  576 [code      ]         )
  577 [return    ]     return report
  578 [blank     ] 
  579 [blank     ] 
  580 [comment   ] # ============================================================ CLI
  581 [branch    ] if __name__ == "__main__":
  582 [import    ]     import sys
  583 [blank     ] 
  584 [branch    ]     if len(sys.argv) < 2:
  585 [code      ]         print("usage: python hit_scorer.py <master.wav> [out.json]")
  586 [code      ]         sys.exit(1)
  587 [code      ]     r = score_track(sys.argv[1], out_json=sys.argv[2] if len(sys.argv) > 2 else None)
  588 [code      ]     print(json.dumps(r, ensure_ascii=False, indent=2))
```
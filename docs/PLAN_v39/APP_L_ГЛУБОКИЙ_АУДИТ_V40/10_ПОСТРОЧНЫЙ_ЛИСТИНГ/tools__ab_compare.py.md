# ПОСТРОЧНЫЙ ЛИСТИНГ: `tools/ab_compare.py`

**Всего строк:** 236

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 127 | 53.8 |
| blank | 29 | 12.3 |
| branch | 17 | 7.2 |
| docstring | 14 | 5.9 |
| return | 14 | 5.9 |
| import | 12 | 5.1 |
| try_block | 8 | 3.4 |
| def | 8 | 3.4 |
| comment | 5 | 2.1 |
| raise | 1 | 0.4 |
| loop | 1 | 0.4 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v15 — tools/ab_compare.py
    3 [docstring ] ==============================================
    4 [docstring ] TZ раздел 20 (A/B сравнение). Сравнивает пользовательский трек
    5 [docstring ] с референсом:
    6 [docstring ]   - LUFS integrated / short-term
    7 [docstring ]   - True Peak (approx)
    8 [docstring ]   - RMS / peak
    9 [docstring ]   - Spectrogram (PNG, side-by-side)
   10 [docstring ]   - Stereo width (mid/side correlation)
   11 [docstring ]   - Duration match
   12 [docstring ] Возвращает JSON и PNG.
   13 [blank     ] 
   14 [docstring ] CLI: python tools/ab_compare.py user.wav ref.wav [--out dir]
   15 [docstring ] """
   16 [blank     ] 
   17 [import    ] from __future__ import annotations
   18 [blank     ] 
   19 [import    ] import argparse
   20 [import    ] import json
   21 [import    ] import sys
   22 [import    ] from pathlib import Path
   23 [import    ] from typing import Any
   24 [blank     ] 
   25 [try_block ] try:
   26 [import    ]     import numpy as np
   27 [import    ]     import pyloudnorm as pyln
   28 [import    ]     import soundfile as sf
   29 [try_block ] except Exception as e:
   30 [code      ]     print(f"[ab_compare] deps missing: {e}", file=sys.stderr)
   31 [raise     ]     raise
   32 [blank     ] 
   33 [try_block ] try:
   34 [import    ]     import matplotlib
   35 [blank     ] 
   36 [code      ]     matplotlib.use("Agg")
   37 [import    ]     import matplotlib.pyplot as plt
   38 [blank     ] 
   39 [code      ]     HAS_PLT = True
   40 [try_block ] except Exception:
   41 [code      ]     HAS_PLT = False
   42 [blank     ] 
   43 [blank     ] 
   44 [def       ] def _load_stereo(path: str):
   45 [code      ]     data, sr = sf.read(path, always_2d=False)
   46 [branch    ]     if data.ndim == 1:
   47 [code      ]         data = np.stack([data, data], axis=1)
   48 [return    ]     return data.astype(np.float32), sr
   49 [blank     ] 
   50 [blank     ] 
   51 [def       ] def _lufs(data, sr):
   52 [try_block ]     try:
   53 [code      ]         meter = pyln.Meter(sr)
   54 [return    ]         return float(meter.integrated_loudness(data))
   55 [try_block ]     except Exception:
   56 [return    ]         return None
   57 [blank     ] 
   58 [blank     ] 
   59 [def       ] def _true_peak_db(data):
   60 [code      ]     peak = float(np.max(np.abs(data))) if data.size else 0.0
   61 [branch    ]     if peak <= 0:
   62 [return    ]         return -120.0
   63 [return    ]     return 20.0 * np.log10(peak)
   64 [blank     ] 
   65 [blank     ] 
   66 [def       ] def _stereo_width(data):
   67 [branch    ]     if data.ndim < 2 or data.shape[1] < 2:
   68 [return    ]         return 0.0
   69 [code      ]     L, R = data[:, 0], data[:, 1]
   70 [comment   ]     # correlation
   71 [branch    ]     if np.std(L) < 1e-9 or np.std(R) < 1e-9:
   72 [return    ]         return 0.0
   73 [code      ]     c = float(np.corrcoef(L, R)[0, 1])
   74 [return    ]     return 1.0 - abs(c)  # ширина = 1 - abs corr
   75 [blank     ] 
   76 [blank     ] 
   77 [def       ] def _spectrogram(data, sr, out_png: Path, title: str):
   78 [branch    ]     if not HAS_PLT:
   79 [return    ]         return False
   80 [code      ]     mono = data.mean(axis=1) if data.ndim > 1 else data
   81 [comment   ]     # STFT
   82 [code      ]     n_fft = 2048
   83 [code      ]     hop = 512
   84 [comment   ]     # numpy-based simple STFT
   85 [import    ]     from numpy.lib.stride_tricks import sliding_window_view
   86 [blank     ] 
   87 [branch    ]     if len(mono) < n_fft:
   88 [return    ]         return False
   89 [code      ]     window = np.hanning(n_fft)
   90 [code      ]     frames = sliding_window_view(mono, n_fft)[::hop]
   91 [code      ]     spec = np.abs(np.fft.rfft(frames * window, axis=1)).T
   92 [code      ]     spec_db = 20.0 * np.log10(spec + 1e-9)
   93 [code      ]     fig, ax = plt.subplots(figsize=(10, 4))
   94 [code      ]     ax.imshow(
   95 [code      ]         spec_db,
   96 [code      ]         aspect="auto",
   97 [code      ]         origin="lower",
   98 [code      ]         extent=[0, len(mono) / sr, 0, sr / 2 / 1000],
   99 [code      ]         cmap="viridis",
  100 [code      ]         vmin=-80,
  101 [code      ]         vmax=0,
  102 [code      ]     )
  103 [code      ]     ax.set_xlabel("Time (s)")
  104 [code      ]     ax.set_ylabel("Freq (kHz)")
  105 [code      ]     ax.set_title(title)
  106 [code      ]     fig.tight_layout()
  107 [code      ]     fig.savefig(out_png, dpi=100)
  108 [code      ]     plt.close(fig)
  109 [return    ]     return True
  110 [blank     ] 
  111 [blank     ] 
  112 [def       ] def compare(user_wav: str, ref_wav: str, out_dir: str) -> dict[str, Any]:
  113 [code      ]     out = Path(out_dir)
  114 [code      ]     out.mkdir(parents=True, exist_ok=True)
  115 [code      ]     u_data, u_sr = _load_stereo(user_wav)
  116 [code      ]     r_data, r_sr = _load_stereo(ref_wav)
  117 [code      ]     u_lufs = _lufs(u_data, u_sr)
  118 [code      ]     r_lufs = _lufs(r_data, r_sr)
  119 [code      ]     u_tp = _true_peak_db(u_data)
  120 [code      ]     r_tp = _true_peak_db(r_data)
  121 [code      ]     u_rms = float(np.sqrt(np.mean(u_data**2)))
  122 [code      ]     r_rms = float(np.sqrt(np.mean(r_data**2)))
  123 [code      ]     u_w = _stereo_width(u_data)
  124 [code      ]     r_w = _stereo_width(r_data)
  125 [code      ]     u_dur = u_data.shape[0] / u_sr
  126 [code      ]     r_dur = r_data.shape[0] / r_sr
  127 [blank     ] 
  128 [code      ]     u_png = out / "spec_user.png"
  129 [code      ]     r_png = out / "spec_ref.png"
  130 [code      ]     _spectrogram(u_data, u_sr, u_png, "USER — spectrogram")
  131 [code      ]     _spectrogram(r_data, r_sr, r_png, "REF  — spectrogram")
  132 [blank     ] 
  133 [comment   ]     # Side-by-side combined
  134 [code      ]     combo_png = None
  135 [branch    ]     if HAS_PLT:
  136 [try_block ]         try:
  137 [code      ]             combo_png = out / "ab_combined.png"
  138 [code      ]             fig, axes = plt.subplots(2, 1, figsize=(12, 6))
  139 [loop      ]             for ax, path, title in ((axes[0], u_png, "USER"), (axes[1], r_png, "REF")):
  140 [branch    ]                 if path.exists():
  141 [code      ]                     img = plt.imread(path)
  142 [code      ]                     ax.imshow(img)
  143 [code      ]                     ax.axis("off")
  144 [code      ]                     ax.set_title(title)
  145 [code      ]             fig.tight_layout()
  146 [code      ]             fig.savefig(combo_png, dpi=100)
  147 [code      ]             plt.close(fig)
  148 [try_block ]         except Exception:
  149 [code      ]             combo_png = None
  150 [blank     ] 
  151 [code      ]     result = {
  152 [code      ]         "user": {
  153 [code      ]             "path": user_wav,
  154 [code      ]             "sr": u_sr,
  155 [code      ]             "duration_sec": round(u_dur, 3),
  156 [code      ]             "lufs_integrated": u_lufs,
  157 [code      ]             "true_peak_dbfs": u_tp,
  158 [code      ]             "rms": u_rms,
  159 [code      ]             "stereo_width": u_w,
  160 [code      ]         },
  161 [code      ]         "ref": {
  162 [code      ]             "path": ref_wav,
  163 [code      ]             "sr": r_sr,
  164 [code      ]             "duration_sec": round(r_dur, 3),
  165 [code      ]             "lufs_integrated": r_lufs,
  166 [code      ]             "true_peak_dbfs": r_tp,
  167 [code      ]             "rms": r_rms,
  168 [code      ]             "stereo_width": r_w,
  169 [code      ]         },
  170 [code      ]         "delta": {
  171 [code      ]             "lufs": (
  172 [code      ]                 round(u_lufs - r_lufs, 2)
  173 [branch    ]                 if u_lufs is not None and r_lufs is not None
  174 [code      ]                 else None
  175 [code      ]             ),
  176 [code      ]             "true_peak_db": round(u_tp - r_tp, 2),
  177 [code      ]             "rms": round(u_rms - r_rms, 4),
  178 [code      ]             "stereo_width": round(u_w - r_w, 3),
  179 [code      ]             "duration_sec": round(u_dur - r_dur, 3),
  180 [code      ]         },
  181 [code      ]         "spectrograms": {
  182 [code      ]             "user": str(u_png) if u_png.exists() else None,
  183 [code      ]             "ref": str(r_png) if r_png.exists() else None,
  184 [code      ]             "combined": str(combo_png) if combo_png else None,
  185 [code      ]         },
  186 [code      ]         "verdict": _verdict(u_lufs, r_lufs, u_tp, r_tp, u_w, r_w),
  187 [code      ]     }
  188 [code      ]     (out / "ab_report.json").write_text(
  189 [code      ]         json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
  190 [code      ]     )
  191 [return    ]     return result
  192 [blank     ] 
  193 [blank     ] 
  194 [def       ] def _verdict(u_l, r_l, u_tp, r_tp, u_w, r_w):
  195 [code      ]     notes = []
  196 [branch    ]     if u_l is not None and r_l is not None:
  197 [code      ]         d = u_l - r_l
  198 [branch    ]         if abs(d) < 1.0:
  199 [code      ]             notes.append(f"✅ LUFS: почти в цель ({d:+.1f}dB)")
  200 [branch    ]         elif d < -1:
  201 [code      ]             notes.append(f"⚠️ USER тише на {-d:.1f}dB")
  202 [branch    ]         else:
  203 [code      ]             notes.append(f"⚠️ USER громче на {d:.1f}dB")
  204 [branch    ]     if u_tp - r_tp > 0.3:
  205 [code      ]         notes.append("⚠️ USER пикует выше — возможен клиппинг")
  206 [branch    ]     if abs(u_w - r_w) > 0.15:
  207 [code      ]         notes.append(f"⚠️ Стерео-ширина отличается на {u_w-r_w:+.2f}")
  208 [branch    ]     if not notes:
  209 [code      ]         notes.append("✅ Треки близки по метрикам")
  210 [return    ]     return notes
  211 [blank     ] 
  212 [blank     ] 
  213 [def       ] def main():
  214 [code      ]     p = argparse.ArgumentParser()
  215 [code      ]     p.add_argument("user_wav")
  216 [code      ]     p.add_argument("ref_wav")
  217 [code      ]     p.add_argument("--out", default="output/ab_compare")
  218 [code      ]     a = p.parse_args()
  219 [code      ]     r = compare(a.user_wav, a.ref_wav, a.out)
  220 [comment   ]     # Печатаем без spectrograms полных путей (короткая версия)
  221 [code      ]     print(
  222 [code      ]         json.dumps(
  223 [code      ]             {
  224 [code      ]                 "delta": r["delta"],
  225 [code      ]                 "verdict": r["verdict"],
  226 [code      ]                 "report_path": str(Path(a.out) / "ab_report.json"),
  227 [code      ]             },
  228 [code      ]             ensure_ascii=False,
  229 [code      ]             indent=2,
  230 [code      ]         )
  231 [code      ]     )
  232 [return    ]     return 0
  233 [blank     ] 
  234 [blank     ] 
  235 [branch    ] if __name__ == "__main__":
  236 [code      ]     sys.exit(main())
```
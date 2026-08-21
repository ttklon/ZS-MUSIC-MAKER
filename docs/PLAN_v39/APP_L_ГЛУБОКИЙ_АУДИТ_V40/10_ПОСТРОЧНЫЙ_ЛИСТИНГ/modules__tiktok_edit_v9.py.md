# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/tiktok_edit_v9.py`

**Всего строк:** 267

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 138 | 51.7 |
| branch | 32 | 12.0 |
| blank | 31 | 11.6 |
| return | 19 | 7.1 |
| docstring | 17 | 6.4 |
| import | 8 | 3.0 |
| def | 8 | 3.0 |
| try_block | 6 | 2.2 |
| comment | 5 | 1.9 |
| loop | 3 | 1.1 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v9] tiktok_edit_v9.py — авто-нарезка TikTok / Reels версий.
    3 [blank     ] 
    4 [docstring ] По ТЗ разделу «...ЗВУЧАТ В ... ТИКТОКЕ»:
    5 [docstring ]   Для каждого трека нужны 3 короткие нарезки:
    6 [docstring ]     • tiktok_15s.wav  — самый вирусный кусок 15 сек с моментальным входом
    7 [docstring ]     • tiktok_30s.wav  — 30 сек версия для Reels/Shorts
    8 [docstring ]     • hook_loop.wav   — только припев (8-16 bars) для эдитов
    9 [blank     ] 
   10 [docstring ] Стартовая позиция берётся из:
   11 [docstring ]   1. hit_scorer.score_track()["tiktok_slice"], если передан
   12 [docstring ]   2. arrangement_plan["tiktok_hook"], если передан
   13 [docstring ]   3. Fallback: находим самый громкий 25-сек кусок
   14 [blank     ] 
   15 [docstring ] Опционально делает вертикальное видео 9:16 с волновой формой через ffmpeg
   16 [docstring ] (если ffmpeg доступен).
   17 [docstring ] """
   18 [blank     ] 
   19 [import    ] from __future__ import annotations
   20 [blank     ] 
   21 [import    ] import json
   22 [import    ] import shutil
   23 [import    ] import subprocess
   24 [import    ] from pathlib import Path
   25 [blank     ] 
   26 [try_block ] try:
   27 [import    ]     import numpy as np
   28 [try_block ] except Exception:
   29 [code      ]     np = None
   30 [blank     ] 
   31 [try_block ] try:
   32 [import    ]     import soundfile as sf
   33 [blank     ] 
   34 [code      ]     HAS_SF = True
   35 [try_block ] except Exception:
   36 [code      ]     HAS_SF = False
   37 [blank     ] 
   38 [blank     ] 
   39 [def       ] def _read(path: str):
   40 [branch    ]     if not HAS_SF:
   41 [return    ]         return None, None
   42 [code      ]     y, sr = sf.read(path, always_2d=True)
   43 [return    ]     return y, sr
   44 [blank     ] 
   45 [blank     ] 
   46 [def       ] def _write(path: str, y, sr):
   47 [code      ]     Path(path).parent.mkdir(parents=True, exist_ok=True)
   48 [code      ]     sf.write(path, y, sr)
   49 [blank     ] 
   50 [blank     ] 
   51 [def       ] def _find_hot_slice(y, sr, want_sec: float = 25.0) -> tuple[float, float]:
   52 [docstring ]     """Находим самый громкий кусок нужной длины."""
   53 [branch    ]     if np is None or len(y) == 0:
   54 [return    ]         return 0.0, want_sec
   55 [branch    ]     if y.ndim == 2:
   56 [code      ]         mono = y.mean(axis=1)
   57 [branch    ]     else:
   58 [code      ]         mono = y
   59 [code      ]     win_len = int(sr * want_sec)
   60 [branch    ]     if len(mono) <= win_len:
   61 [return    ]         return 0.0, len(mono) / sr
   62 [code      ]     hop = int(sr * 1.0)
   63 [code      ]     best_rms = 0.0
   64 [code      ]     best_start = 0
   65 [loop      ]     for i in range(0, len(mono) - win_len, hop):
   66 [code      ]         r = float(np.sqrt(np.mean(mono[i : i + win_len] ** 2) + 1e-12))
   67 [branch    ]         if r > best_rms:
   68 [code      ]             best_rms = r
   69 [code      ]             best_start = i
   70 [return    ]     return best_start / sr, (best_start + win_len) / sr
   71 [blank     ] 
   72 [blank     ] 
   73 [def       ] def _fade_in_out(y, sr, in_ms: float = 40.0, out_ms: float = 120.0):
   74 [branch    ]     if np is None:
   75 [return    ]         return y
   76 [code      ]     in_n = int(sr * in_ms / 1000.0)
   77 [code      ]     out_n = int(sr * out_ms / 1000.0)
   78 [branch    ]     if in_n < len(y):
   79 [code      ]         ramp = np.linspace(0.0, 1.0, in_n)
   80 [branch    ]         if y.ndim == 2:
   81 [code      ]             y[:in_n, :] = y[:in_n, :] * ramp[:, None]
   82 [branch    ]         else:
   83 [code      ]             y[:in_n] = y[:in_n] * ramp
   84 [branch    ]     if out_n < len(y):
   85 [code      ]         ramp = np.linspace(1.0, 0.0, out_n)
   86 [branch    ]         if y.ndim == 2:
   87 [code      ]             y[-out_n:, :] = y[-out_n:, :] * ramp[:, None]
   88 [branch    ]         else:
   89 [code      ]             y[-out_n:] = y[-out_n:] * ramp
   90 [return    ]     return y
   91 [blank     ] 
   92 [blank     ] 
   93 [def       ] def cut_slice(
   94 [code      ]     input_wav: str, output_wav: str, start_sec: float, end_sec: float, fade: bool = True
   95 [code      ] ) -> dict:
   96 [branch    ]     if not HAS_SF or np is None:
   97 [return    ]         return {"ok": False, "error": "soundfile/numpy required"}
   98 [code      ]     y, sr = _read(input_wav)
   99 [branch    ]     if y is None:
  100 [return    ]         return {"ok": False, "error": "read failed"}
  101 [code      ]     s = max(0, int(start_sec * sr))
  102 [code      ]     e = min(len(y), int(end_sec * sr))
  103 [branch    ]     if e <= s:
  104 [return    ]         return {"ok": False, "error": "invalid slice"}
  105 [code      ]     seg = y[s:e].copy()
  106 [branch    ]     if fade:
  107 [code      ]         seg = _fade_in_out(seg, sr)
  108 [code      ]     _write(output_wav, seg, sr)
  109 [return    ]     return {
  110 [code      ]         "ok": True,
  111 [code      ]         "output": output_wav,
  112 [code      ]         "duration_s": round((e - s) / sr, 2),
  113 [code      ]         "start_sec": start_sec,
  114 [code      ]         "end_sec": end_sec,
  115 [code      ]     }
  116 [blank     ] 
  117 [blank     ] 
  118 [def       ] def make_all_cuts(
  119 [code      ]     input_wav: str,
  120 [code      ]     out_dir: str,
  121 [code      ]     hit_report: dict | None = None,
  122 [code      ]     arrangement_plan: dict | None = None,
  123 [code      ] ) -> dict:
  124 [docstring ]     """Основной API. Делает 15s, 30s и hook_loop."""
  125 [branch    ]     if not HAS_SF or np is None:
  126 [return    ]         return {"ok": False, "error": "soundfile/numpy required"}
  127 [code      ]     y, sr = _read(input_wav)
  128 [branch    ]     if y is None:
  129 [return    ]         return {"ok": False, "error": "read failed"}
  130 [blank     ] 
  131 [code      ]     dur = len(y) / sr
  132 [code      ]     outd = Path(out_dir)
  133 [code      ]     outd.mkdir(parents=True, exist_ok=True)
  134 [blank     ] 
  135 [comment   ]     # Стартовая точка
  136 [code      ]     start = None
  137 [branch    ]     if hit_report and "tiktok_slice" in hit_report:
  138 [code      ]         start = float(hit_report["tiktok_slice"].get("start_sec", 0.0))
  139 [branch    ]     elif arrangement_plan and "tiktok_hook" in arrangement_plan:
  140 [code      ]         start = float(arrangement_plan["tiktok_hook"].get("start_sec", 0.0))
  141 [branch    ]     if start is None:
  142 [code      ]         start, _ = _find_hot_slice(y, sr, want_sec=25.0)
  143 [blank     ] 
  144 [code      ]     results = {}
  145 [comment   ]     # 15s
  146 [code      ]     s15 = max(0.0, min(dur - 15.0, start))
  147 [code      ]     results["tiktok_15s"] = cut_slice(
  148 [code      ]         input_wav, str(outd / "tiktok_15s.wav"), s15, s15 + 15.0
  149 [code      ]     )
  150 [comment   ]     # 30s
  151 [code      ]     s30 = max(0.0, min(dur - 30.0, start - 2.0))
  152 [code      ]     results["tiktok_30s"] = cut_slice(
  153 [code      ]         input_wav, str(outd / "tiktok_30s.wav"), s30, s30 + 30.0
  154 [code      ]     )
  155 [comment   ]     # hook_loop — попытка взять припев из аранжировки
  156 [code      ]     hook_start, hook_end = None, None
  157 [branch    ]     if arrangement_plan and arrangement_plan.get("sections"):
  158 [code      ]         chorus = [
  159 [code      ]             s
  160 [loop      ]             for s in arrangement_plan["sections"]
  161 [branch    ]             if s.get("name", "").startswith(("chorus", "drop"))
  162 [code      ]         ]
  163 [branch    ]         if chorus:
  164 [code      ]             best = max(chorus, key=lambda s: s.get("energy", 0.5))
  165 [code      ]             hook_start = float(best["start_sec"])
  166 [code      ]             hook_end = float(best["end_sec"])
  167 [branch    ]     if hook_start is None:
  168 [code      ]         hook_start, hook_end = start, min(dur, start + 16.0)
  169 [code      ]     results["hook_loop"] = cut_slice(
  170 [code      ]         input_wav, str(outd / "hook_loop.wav"), hook_start, hook_end
  171 [code      ]     )
  172 [blank     ] 
  173 [return    ]     return {
  174 [code      ]         "ok": True,
  175 [code      ]         "dir": str(outd),
  176 [code      ]         "results": results,
  177 [code      ]         "auto_start_sec": round(start, 2),
  178 [code      ]         "src_duration": round(dur, 2),
  179 [code      ]     }
  180 [blank     ] 
  181 [blank     ] 
  182 [comment   ] # ============================================================ video (optional)
  183 [def       ] def _has_ffmpeg() -> bool:
  184 [return    ]     return shutil.which("ffmpeg") is not None
  185 [blank     ] 
  186 [blank     ] 
  187 [def       ] def make_vertical_video(
  188 [code      ]     audio_wav: str,
  189 [code      ]     output_mp4: str,
  190 [code      ]     cover_png: str | None = None,
  191 [code      ]     bg_color: str = "black",
  192 [code      ] ) -> dict:
  193 [docstring ]     """Создаёт вертикальный 9:16 mp4 с волновой формой + обложкой (если есть)."""
  194 [branch    ]     if not _has_ffmpeg():
  195 [return    ]         return {"ok": False, "error": "ffmpeg not available"}
  196 [code      ]     Path(output_mp4).parent.mkdir(parents=True, exist_ok=True)
  197 [branch    ]     if cover_png and Path(cover_png).exists():
  198 [code      ]         cmd = [
  199 [code      ]             "ffmpeg",
  200 [code      ]             "-y",
  201 [code      ]             "-loop",
  202 [code      ]             "1",
  203 [code      ]             "-i",
  204 [code      ]             str(cover_png),
  205 [code      ]             "-i",
  206 [code      ]             str(audio_wav),
  207 [code      ]             "-c:v",
  208 [code      ]             "libx264",
  209 [code      ]             "-tune",
  210 [code      ]             "stillimage",
  211 [code      ]             "-c:a",
  212 [code      ]             "aac",
  213 [code      ]             "-b:a",
  214 [code      ]             "192k",
  215 [code      ]             "-shortest",
  216 [code      ]             "-vf",
  217 [code      ]             "scale=1080:1920:force_original_aspect_ratio=increase," "crop=1080:1920",
  218 [code      ]             "-pix_fmt",
  219 [code      ]             "yuv420p",
  220 [code      ]             str(output_mp4),
  221 [code      ]         ]
  222 [branch    ]     else:
  223 [code      ]         cmd = [
  224 [code      ]             "ffmpeg",
  225 [code      ]             "-y",
  226 [code      ]             "-i",
  227 [code      ]             str(audio_wav),
  228 [code      ]             "-filter_complex",
  229 [code      ]             "[0:a]showwaves=s=1080x1920:mode=cline:colors=cyan," "format=yuv420p[v]",
  230 [code      ]             "-map",
  231 [code      ]             "[v]",
  232 [code      ]             "-map",
  233 [code      ]             "0:a",
  234 [code      ]             "-c:v",
  235 [code      ]             "libx264",
  236 [code      ]             "-c:a",
  237 [code      ]             "aac",
  238 [code      ]             "-b:a",
  239 [code      ]             "192k",
  240 [code      ]             "-shortest",
  241 [code      ]             str(output_mp4),
  242 [code      ]         ]
  243 [try_block ]     try:
  244 [code      ]         p = subprocess.run(cmd, capture_output=True, timeout=180)
  245 [branch    ]         if p.returncode != 0:
  246 [return    ]             return {"ok": False, "error": p.stderr[-500:].decode("utf-8", "ignore")}
  247 [return    ]         return {"ok": True, "output": output_mp4}
  248 [try_block ]     except Exception as e:
  249 [return    ]         return {"ok": False, "error": str(e)}
  250 [blank     ] 
  251 [blank     ] 
  252 [branch    ] if __name__ == "__main__":
  253 [import    ]     import sys
  254 [blank     ] 
  255 [branch    ]     if len(sys.argv) < 3:
  256 [code      ]         print("usage: python tiktok_edit_v9.py <in.wav> <out_dir>")
  257 [code      ]         sys.exit(1)
  258 [code      ]     r = make_all_cuts(sys.argv[1], sys.argv[2])
  259 [code      ]     print(
  260 [code      ]         json.dumps(
  261 [code      ]             {
  262 [code      ]                 k: (v.get("output"), v.get("duration_s"))
  263 [loop      ]                 for k, v in r.get("results", {}).items()
  264 [code      ]             },
  265 [code      ]             indent=2,
  266 [code      ]         )
  267 [code      ]     )
```
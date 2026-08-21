# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/video_edit_v11.py`

**Всего строк:** 464

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 265 | 57.1 |
| blank | 44 | 9.5 |
| branch | 40 | 8.6 |
| try_block | 26 | 5.6 |
| return | 25 | 5.4 |
| def | 16 | 3.4 |
| loop | 13 | 2.8 |
| docstring | 11 | 2.4 |
| import | 11 | 2.4 |
| stmt | 6 | 1.3 |
| decorator | 2 | 0.4 |
| class | 2 | 0.4 |
| comment | 2 | 0.4 |
| raise | 1 | 0.2 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v11 — video_edit_v11.py
    3 [blank     ] 
    4 [docstring ] TikTok / Reels / YouTube-Shorts автогенератор MP4 из финального master.wav
    5 [docstring ] + обложки cover.png. Реализует ТЗ 20.2 п.32-33.
    6 [blank     ] 
    7 [docstring ] Backends:
    8 [docstring ] - moviepy + ffmpeg → реальный H.264/AAC MP4 с beat-glow, LRC-overlay
    9 [docstring ] - fallback: HOOK.wav + build_manually.txt с готовой ffmpeg-командой
   10 [blank     ] 
   11 [docstring ] Никогда не крашится, работает на слабом железе (CPU-only).
   12 [docstring ] UTF-8 в коде.
   13 [docstring ] """
   14 [blank     ] 
   15 [import    ] from __future__ import annotations
   16 [blank     ] 
   17 [import    ] import json
   18 [import    ] import math
   19 [import    ] import os
   20 [import    ] import struct
   21 [import    ] import sys
   22 [import    ] import wave
   23 [import    ] from dataclasses import asdict, dataclass
   24 [blank     ] 
   25 [blank     ] 
   26 [def       ] def _safe_print(msg: str) -> None:
   27 [try_block ]     try:
   28 [code      ]         print(msg)
   29 [try_block ]     except UnicodeEncodeError:
   30 [code      ]         sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))
   31 [blank     ] 
   32 [blank     ] 
   33 [decorator ] @dataclass
   34 [class     ] class VideoEditRequest:
   35 [code      ]     master_wav: str
   36 [code      ]     cover_png: str | None = None
   37 [code      ]     lyrics_lrc: str | None = None
   38 [code      ]     bpm: float = 140.0
   39 [code      ]     duration_sec: int = 20
   40 [code      ]     orientation: str = "vertical"  # vertical | horizontal | square
   41 [code      ]     output_path: str = "output/tiktok_edit.mp4"
   42 [code      ]     title: str = ""
   43 [code      ]     artist: str = ""
   44 [code      ]     beat_glow: bool = True
   45 [code      ]     waveform_bar: bool = True
   46 [code      ]     lyrics_overlay: bool = True
   47 [blank     ] 
   48 [def       ]     def resolution(self) -> tuple[int, int]:
   49 [branch    ]         if self.orientation == "vertical":
   50 [return    ]             return (1080, 1920)
   51 [branch    ]         if self.orientation == "horizontal":
   52 [return    ]             return (1920, 1080)
   53 [return    ]         return (1080, 1080)
   54 [blank     ] 
   55 [blank     ] 
   56 [decorator ] @dataclass
   57 [class     ] class VideoEditResult:
   58 [code      ]     ok: bool
   59 [code      ]     output_path: str
   60 [code      ]     duration_sec: float
   61 [code      ]     resolution: tuple[int, int]
   62 [code      ]     backend: str
   63 [code      ]     hook_start_sec: float
   64 [code      ]     reason: str = ""
   65 [blank     ] 
   66 [def       ]     def to_dict(self) -> dict:
   67 [code      ]         d = asdict(self)
   68 [code      ]         d["resolution"] = list(self.resolution)
   69 [return    ]         return d
   70 [blank     ] 
   71 [blank     ] 
   72 [def       ] def _read_wav_mono(path: str) -> tuple[list[float], int]:
   73 [stmt      ]     with wave.open(path, "rb") as wf:
   74 [code      ]         n_ch = wf.getnchannels()
   75 [code      ]         sw = wf.getsampwidth()
   76 [code      ]         sr = wf.getframerate()
   77 [code      ]         n = wf.getnframes()
   78 [code      ]         frames = wf.readframes(n)
   79 [branch    ]     if sw == 2:
   80 [code      ]         count = n * n_ch
   81 [code      ]         samples = struct.unpack("<" + "h" * count, frames)
   82 [branch    ]         if n_ch == 1:
   83 [code      ]             mono = [s / 32768.0 for s in samples]
   84 [branch    ]         else:
   85 [code      ]             mono = []
   86 [loop      ]             for i in range(0, count, n_ch):
   87 [code      ]                 s = sum(samples[i : i + n_ch]) / n_ch
   88 [code      ]                 mono.append(s / 32768.0)
   89 [branch    ]     elif sw == 3:
   90 [code      ]         mono = []
   91 [code      ]         step = 3 * n_ch
   92 [loop      ]         for i in range(0, len(frames), step):
   93 [code      ]             channels = []
   94 [loop      ]             for c in range(n_ch):
   95 [code      ]                 off = i + c * 3
   96 [code      ]                 b = frames[off : off + 3]
   97 [branch    ]                 if len(b) < 3:
   98 [code      ]                     channels.append(0)
   99 [code      ]                     continue
  100 [code      ]                 val = int.from_bytes(b, "little", signed=True)
  101 [code      ]                 channels.append(val / (1 << 23))
  102 [code      ]             mono.append(sum(channels) / max(1, n_ch))
  103 [branch    ]     elif sw == 4:
  104 [code      ]         count = n * n_ch
  105 [code      ]         samples = struct.unpack("<" + "i" * count, frames)
  106 [code      ]         norm = float(1 << 31)
  107 [branch    ]         if n_ch == 1:
  108 [code      ]             mono = [s / norm for s in samples]
  109 [branch    ]         else:
  110 [code      ]             mono = []
  111 [loop      ]             for i in range(0, count, n_ch):
  112 [code      ]                 s = sum(samples[i : i + n_ch]) / n_ch
  113 [code      ]                 mono.append(s / norm)
  114 [branch    ]     else:
  115 [raise     ]         raise ValueError(f"Unsupported sample width: {sw}")
  116 [return    ]     return mono, sr
  117 [blank     ] 
  118 [blank     ] 
  119 [def       ] def _rms_windows(samples: list[float], sr: int, win_sec: float = 1.0) -> list[float]:
  120 [code      ]     win = max(1, int(sr * win_sec))
  121 [code      ]     out = []
  122 [loop      ]     for i in range(0, len(samples), win):
  123 [code      ]         chunk = samples[i : i + win]
  124 [branch    ]         if not chunk:
  125 [code      ]             continue
  126 [code      ]         s = sum(x * x for x in chunk) / len(chunk)
  127 [code      ]         out.append(math.sqrt(s))
  128 [return    ]     return out
  129 [blank     ] 
  130 [blank     ] 
  131 [def       ] def detect_hook(master_wav: str, target_sec: int = 20) -> tuple[float, float]:
  132 [docstring ]     """Возвращает (start_sec, end_sec) для самого «мясного» куска."""
  133 [try_block ]     try:
  134 [code      ]         samples, sr = _read_wav_mono(master_wav)
  135 [try_block ]     except Exception as e:
  136 [code      ]         _safe_print(f"[video_edit_v11] hook detect fail: {e}")
  137 [return    ]         return (0.0, float(target_sec))
  138 [code      ]     total = len(samples) / sr
  139 [branch    ]     if total <= target_sec + 1:
  140 [return    ]         return (0.0, total)
  141 [code      ]     rms = _rms_windows(samples, sr, win_sec=1.0)
  142 [code      ]     w = target_sec
  143 [branch    ]     if w >= len(rms):
  144 [return    ]         return (0.0, float(target_sec))
  145 [code      ]     best_sum = -1.0
  146 [code      ]     best_start = 0
  147 [code      ]     running = sum(rms[:w])
  148 [branch    ]     if running > best_sum:
  149 [code      ]         best_sum, best_start = running, 0
  150 [loop      ]     for i in range(1, len(rms) - w + 1):
  151 [code      ]         running += rms[i + w - 1] - rms[i - 1]
  152 [branch    ]         if running > best_sum:
  153 [code      ]             best_sum, best_start = running, i
  154 [comment   ]     # Prefer second half — избегаем интро
  155 [branch    ]     if best_start < 0.25 * len(rms):
  156 [code      ]         half = len(rms) // 2
  157 [branch    ]         if half + w <= len(rms):
  158 [code      ]             alt_best = sum(rms[half : half + w])
  159 [code      ]             alt_start = half
  160 [code      ]             running = alt_best
  161 [loop      ]             for i in range(half + 1, len(rms) - w + 1):
  162 [code      ]                 running += rms[i + w - 1] - rms[i - 1]
  163 [branch    ]                 if running > alt_best:
  164 [code      ]                     alt_best, alt_start = running, i
  165 [branch    ]             if alt_best >= 0.85 * best_sum:
  166 [code      ]                 best_start = alt_start
  167 [return    ]     return (float(best_start), float(best_start + w))
  168 [blank     ] 
  169 [blank     ] 
  170 [def       ] def _parse_lrc(lrc_path: str) -> list[tuple[float, str]]:
  171 [code      ]     out = []
  172 [try_block ]     try:
  173 [stmt      ]         with open(lrc_path, "r", encoding="utf-8", errors="ignore") as f:
  174 [loop      ]             for line in f:
  175 [code      ]                 line = line.strip()
  176 [branch    ]                 if not line or not line.startswith("["):
  177 [code      ]                     continue
  178 [code      ]                 end = line.rfind("]")
  179 [branch    ]                 if end < 0:
  180 [code      ]                     continue
  181 [code      ]                 head, text = line[: end + 1], line[end + 1 :].strip()
  182 [code      ]                 i = 0
  183 [loop      ]                 while i < len(head):
  184 [branch    ]                     if head[i] == "[":
  185 [code      ]                         j = head.find("]", i)
  186 [branch    ]                         if j < 0:
  187 [code      ]                             break
  188 [code      ]                         tag = head[i + 1 : j]
  189 [branch    ]                         if ":" in tag and any(c.isdigit() for c in tag):
  190 [try_block ]                             try:
  191 [code      ]                                 m, s = tag.split(":", 1)
  192 [code      ]                                 secs = float(m) * 60 + float(s)
  193 [code      ]                                 out.append((secs, text))
  194 [try_block ]                             except Exception:
  195 [code      ]                                 pass
  196 [code      ]                         i = j + 1
  197 [branch    ]                     else:
  198 [code      ]                         i += 1
  199 [try_block ]     except Exception as e:
  200 [code      ]         _safe_print(f"[video_edit_v11] lrc parse fail: {e}")
  201 [code      ]     out.sort(key=lambda x: x[0])
  202 [return    ]     return out
  203 [blank     ] 
  204 [blank     ] 
  205 [def       ] def _try_moviepy():
  206 [try_block ]     try:
  207 [import    ]         import moviepy.editor as mpy
  208 [blank     ] 
  209 [return    ]         return mpy
  210 [try_block ]     except Exception as e:
  211 [code      ]         _safe_print(f"[video_edit_v11] moviepy not available ({e})")
  212 [return    ]         return None
  213 [blank     ] 
  214 [blank     ] 
  215 [def       ] def _try_pil():
  216 [try_block ]     try:
  217 [import    ]         from PIL import Image, ImageDraw, ImageFilter, ImageFont
  218 [blank     ] 
  219 [return    ]         return (Image, ImageDraw, ImageFont, ImageFilter)
  220 [try_block ]     except Exception:
  221 [return    ]         return None
  222 [blank     ] 
  223 [blank     ] 
  224 [def       ] def _make_static_bg(cover_path: str | None, size: tuple[int, int]):
  225 [code      ]     pil = _try_pil()
  226 [branch    ]     if not pil:
  227 [return    ]         return None
  228 [code      ]     Image, ImageDraw, _ImageFont, ImageFilter = pil
  229 [code      ]     w, h = size
  230 [branch    ]     if cover_path and os.path.exists(cover_path):
  231 [try_block ]         try:
  232 [code      ]             cover = Image.open(cover_path).convert("RGB")
  233 [try_block ]         except Exception:
  234 [code      ]             cover = Image.new("RGB", (1400, 1400), (14, 14, 22))
  235 [branch    ]     else:
  236 [code      ]         cover = Image.new("RGB", (1400, 1400), (14, 14, 22))
  237 [code      ]     bg = cover.resize((w, h)).filter(ImageFilter.GaussianBlur(radius=48))
  238 [code      ]     dark = Image.new("RGB", (w, h), (0, 0, 0))
  239 [code      ]     bg = Image.blend(bg, dark, 0.45)
  240 [code      ]     side = int(min(w, h) * 0.78)
  241 [code      ]     cover_sq = cover.resize((side, side))
  242 [code      ]     x = (w - side) // 2
  243 [code      ]     y = (h - side) // 2 - int(h * 0.05)
  244 [code      ]     bg.paste(cover_sq, (x, y))
  245 [return    ]     return bg
  246 [blank     ] 
  247 [blank     ] 
  248 [def       ] def _draw_title(bg_img, title: str, artist: str, size: tuple[int, int]):
  249 [code      ]     pil = _try_pil()
  250 [branch    ]     if not pil or bg_img is None:
  251 [return    ]         return bg_img
  252 [code      ]     Image, ImageDraw, ImageFont, _ = pil
  253 [code      ]     w, h = size
  254 [code      ]     draw = ImageDraw.Draw(bg_img)
  255 [comment   ]     # v39.4 (ШАГ 002): единый font_utils, hardcoded C:\Windows\Fonts убран
  256 [import    ]     from app.core.font_utils import load_pil_font
  257 [code      ]     font_big = load_pil_font(int(h * 0.045), bold=True)
  258 [code      ]     font_small = load_pil_font(int(h * 0.028), bold=True)
  259 [branch    ]     if artist:
  260 [code      ]         draw.text(
  261 [code      ]             (w * 0.06, h * 0.06), artist.upper(), fill=(240, 240, 240), font=font_small
  262 [code      ]         )
  263 [branch    ]     if title:
  264 [code      ]         draw.text((w * 0.06, h * 0.87), title, fill=(255, 220, 90), font=font_big)
  265 [return    ]     return bg_img
  266 [blank     ] 
  267 [blank     ] 
  268 [def       ] def build_video(req: VideoEditRequest) -> VideoEditResult:
  269 [code      ]     os.makedirs(os.path.dirname(os.path.abspath(req.output_path)) or ".", exist_ok=True)
  270 [code      ]     tmp_dir = os.path.join(
  271 [code      ]         os.path.dirname(os.path.abspath(req.output_path)) or ".", "_v11_tmp"
  272 [code      ]     )
  273 [code      ]     os.makedirs(tmp_dir, exist_ok=True)
  274 [code      ]     hook_start, hook_end = detect_hook(req.master_wav, req.duration_sec)
  275 [code      ]     _safe_print(f"[video_edit_v11] hook: {hook_start:.1f}s -> {hook_end:.1f}s")
  276 [blank     ] 
  277 [code      ]     mpy = _try_moviepy()
  278 [branch    ]     if mpy is not None:
  279 [try_block ]         try:
  280 [return    ]             return _build_with_moviepy(req, hook_start, hook_end, tmp_dir, mpy)
  281 [try_block ]         except Exception as e:
  282 [code      ]             _safe_print(f"[video_edit_v11] moviepy render failed: {e}")
  283 [return    ]     return _build_fallback(req, hook_start, hook_end)
  284 [blank     ] 
  285 [blank     ] 
  286 [def       ] def _build_with_moviepy(req, hook_start, hook_end, tmp_dir, mpy) -> VideoEditResult:
  287 [code      ]     size = req.resolution()
  288 [code      ]     duration = float(hook_end - hook_start)
  289 [code      ]     audio = mpy.AudioFileClip(req.master_wav).subclip(hook_start, hook_end)
  290 [code      ]     bg_img = _make_static_bg(req.cover_png, size)
  291 [code      ]     bg_img = _draw_title(bg_img, req.title, req.artist, size)
  292 [code      ]     bg_png = None
  293 [branch    ]     if bg_img is not None:
  294 [code      ]         bg_png = os.path.join(tmp_dir, "v11_bg.png")
  295 [code      ]         bg_img.save(bg_png, "PNG")
  296 [branch    ]     if bg_png:
  297 [code      ]         base_clip = mpy.ImageClip(bg_png).set_duration(duration)
  298 [branch    ]     else:
  299 [code      ]         base_clip = mpy.ColorClip(size=size, color=(14, 14, 22)).set_duration(duration)
  300 [code      ]     clips = [base_clip]
  301 [branch    ]     if req.beat_glow and req.bpm > 40:
  302 [code      ]         beat_sec = 60.0 / req.bpm
  303 [code      ]         t = 0.0
  304 [loop      ]         while t < duration:
  305 [code      ]             pulse = (
  306 [code      ]                 mpy.ColorClip(size=size, color=(255, 60, 40))
  307 [code      ]                 .set_opacity(0.14)
  308 [code      ]                 .set_start(t)
  309 [code      ]                 .set_duration(min(0.12, duration - t))
  310 [code      ]             )
  311 [code      ]             clips.append(pulse)
  312 [code      ]             t += beat_sec
  313 [branch    ]     if req.lyrics_overlay and req.lyrics_lrc and os.path.exists(req.lyrics_lrc):
  314 [loop      ]         for t, text in _parse_lrc(req.lyrics_lrc):
  315 [branch    ]             if not text.strip() or t < hook_start or t > hook_end:
  316 [code      ]                 continue
  317 [code      ]             local_t = t - hook_start
  318 [try_block ]             try:
  319 [code      ]                 txt = (
  320 [code      ]                     mpy.TextClip(
  321 [code      ]                         text[:80],
  322 [code      ]                         fontsize=int(size[1] * 0.042),
  323 [code      ]                         color="white",
  324 [code      ]                         method="label",
  325 [code      ]                         stroke_color="black",
  326 [code      ]                         stroke_width=2,
  327 [code      ]                     )
  328 [code      ]                     .set_position(("center", int(size[1] * 0.5)))
  329 [code      ]                     .set_start(local_t)
  330 [code      ]                     .set_duration(min(3.0, hook_end - t))
  331 [code      ]                 )
  332 [code      ]                 clips.append(txt)
  333 [try_block ]             except Exception as e:
  334 [code      ]                 _safe_print(f"[video_edit_v11] textclip fail: {e}")
  335 [code      ]                 break
  336 [code      ]     final = mpy.CompositeVideoClip(clips, size=size).set_audio(audio)
  337 [try_block ]     try:
  338 [code      ]         final.write_videofile(
  339 [code      ]             req.output_path,
  340 [code      ]             fps=24,
  341 [code      ]             codec="libx264",
  342 [code      ]             audio_codec="aac",
  343 [code      ]             preset="medium",
  344 [code      ]             threads=2,
  345 [code      ]             logger=None,
  346 [code      ]             verbose=False,
  347 [code      ]         )
  348 [try_block ]     finally:
  349 [try_block ]         try:
  350 [code      ]             final.close()
  351 [code      ]             audio.close()
  352 [try_block ]         except Exception:
  353 [code      ]             pass
  354 [return    ]     return VideoEditResult(
  355 [code      ]         ok=True,
  356 [code      ]         output_path=req.output_path,
  357 [code      ]         duration_sec=duration,
  358 [code      ]         resolution=size,
  359 [code      ]         backend="moviepy",
  360 [code      ]         hook_start_sec=hook_start,
  361 [code      ]         reason="ok",
  362 [code      ]     )
  363 [blank     ] 
  364 [blank     ] 
  365 [def       ] def _build_fallback(req, hook_start, hook_end) -> VideoEditResult:
  366 [code      ]     out_path = req.output_path
  367 [code      ]     wav_out = os.path.splitext(out_path)[0] + "_HOOK.wav"
  368 [code      ]     backend = "fallback_txt"
  369 [try_block ]     try:
  370 [code      ]         samples, sr = _read_wav_mono(req.master_wav)
  371 [code      ]         s = int(hook_start * sr)
  372 [code      ]         e = int(hook_end * sr)
  373 [code      ]         cut = samples[s:e]
  374 [stmt      ]         with wave.open(wav_out, "wb") as wf:
  375 [code      ]             wf.setnchannels(1)
  376 [code      ]             wf.setsampwidth(2)
  377 [code      ]             wf.setframerate(sr)
  378 [code      ]             wf.writeframes(
  379 [code      ]                 b"".join(
  380 [code      ]                     struct.pack("<h", max(-32768, min(32767, int(x * 32767))))
  381 [loop      ]                     for x in cut
  382 [code      ]                 )
  383 [code      ]             )
  384 [code      ]         backend = "fallback_wav"
  385 [try_block ]     except Exception as e:
  386 [code      ]         _safe_print(f"[video_edit_v11] fallback wav cut failed: {e}")
  387 [code      ]         wav_out = ""
  388 [code      ]     txt_path = os.path.splitext(out_path)[0] + "_build_manually.txt"
  389 [try_block ]     try:
  390 [stmt      ]         with open(txt_path, "w", encoding="utf-8") as f:
  391 [code      ]             f.write("ZS Music Maker v11 — TikTok/Reels edit fallback\n")
  392 [code      ]             f.write(f"master:     {req.master_wav}\n")
  393 [code      ]             f.write(f"cover:      {req.cover_png}\n")
  394 [code      ]             f.write(f"lyrics:     {req.lyrics_lrc}\n")
  395 [code      ]             f.write(f"bpm:        {req.bpm}\n")
  396 [code      ]             f.write(f"hook:       {hook_start:.2f}s .. {hook_end:.2f}s\n")
  397 [code      ]             f.write(f"resolution: {req.resolution()}\n\n")
  398 [code      ]             f.write("Install moviepy+ffmpeg:\n")
  399 [code      ]             f.write("    pip install moviepy imageio-ffmpeg\n")
  400 [code      ]             f.write("Or manually via ffmpeg:\n")
  401 [code      ]             f.write(
  402 [code      ]                 f"ffmpeg -ss {hook_start:.2f} -t {req.duration_sec} "
  403 [code      ]                 f'-i "{req.master_wav}" -loop 1 -i "{req.cover_png}" '
  404 [code      ]                 "-c:v libx264 -c:a aac -shortest -pix_fmt yuv420p "
  405 [code      ]                 f'-vf "scale={req.resolution()[0]}:{req.resolution()[1]}'
  406 [code      ]                 f":force_original_aspect_ratio=increase,crop="
  407 [code      ]                 f'{req.resolution()[0]}:{req.resolution()[1]}" '
  408 [code      ]                 f'"{out_path}"\n'
  409 [code      ]             )
  410 [try_block ]     except Exception as e:
  411 [code      ]         _safe_print(f"[video_edit_v11] fallback txt write failed: {e}")
  412 [return    ]     return VideoEditResult(
  413 [code      ]         ok=False,
  414 [code      ]         output_path=wav_out or txt_path,
  415 [code      ]         duration_sec=hook_end - hook_start,
  416 [code      ]         resolution=req.resolution(),
  417 [code      ]         backend=backend,
  418 [code      ]         hook_start_sec=hook_start,
  419 [code      ]         reason="moviepy/ffmpeg unavailable",
  420 [code      ]     )
  421 [blank     ] 
  422 [blank     ] 
  423 [def       ] def build_release_edits(
  424 [code      ]     master_wav, cover_png, lyrics_lrc, bpm, title, artist, out_dir
  425 [code      ] ) -> dict:
  426 [code      ]     os.makedirs(out_dir, exist_ok=True)
  427 [code      ]     manifest = {}
  428 [loop      ]     for name, orient, dur in [
  429 [code      ]         ("tiktok_edit.mp4", "vertical", 20),
  430 [code      ]         ("reels_edit.mp4", "vertical", 30),
  431 [code      ]         ("shorts_edit.mp4", "vertical", 20),
  432 [code      ]     ]:
  433 [code      ]         req = VideoEditRequest(
  434 [code      ]             master_wav=master_wav,
  435 [code      ]             cover_png=cover_png,
  436 [code      ]             lyrics_lrc=lyrics_lrc,
  437 [code      ]             bpm=bpm,
  438 [code      ]             duration_sec=dur,
  439 [code      ]             orientation=orient,
  440 [code      ]             output_path=os.path.join(out_dir, name),
  441 [code      ]             title=title,
  442 [code      ]             artist=artist,
  443 [code      ]         )
  444 [code      ]         manifest[name] = build_video(req).to_dict()
  445 [stmt      ]     with open(
  446 [code      ]         os.path.join(out_dir, "video_edits_manifest.json"), "w", encoding="utf-8"
  447 [code      ]     ) as f:
  448 [code      ]         json.dump(manifest, f, ensure_ascii=False, indent=2)
  449 [return    ]     return manifest
  450 [blank     ] 
  451 [blank     ] 
  452 [def       ] def _self_test() -> bool:
  453 [code      ]     tmp = "/tmp/_v11_lrc_test.lrc"
  454 [stmt      ]     with open(tmp, "w", encoding="utf-8") as f:
  455 [code      ]         f.write("[00:01.00]hello\n[00:02.50]world\n[bad]skip\n")
  456 [code      ]     parsed = _parse_lrc(tmp)
  457 [code      ]     ok = len(parsed) == 2 and parsed[0][1] == "hello"
  458 [code      ]     rms = _rms_windows([0.0] * 44100 + [0.5] * 44100, 44100, 1.0)
  459 [code      ]     ok &= len(rms) == 2 and rms[1] > rms[0]
  460 [return    ]     return ok
  461 [blank     ] 
  462 [blank     ] 
  463 [branch    ] if __name__ == "__main__":
  464 [code      ]     print("video_edit_v11 self-test:", "OK" if _self_test() else "FAIL")
```
# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/release_pack_full.py`

**Всего строк:** 952

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 502 | 52.7 |
| docstring | 98 | 10.3 |
| blank | 95 | 10.0 |
| branch | 62 | 6.5 |
| try_block | 48 | 5.0 |
| comment | 41 | 4.3 |
| return | 40 | 4.2 |
| def | 23 | 2.4 |
| import | 21 | 2.2 |
| loop | 17 | 1.8 |
| raise | 3 | 0.3 |
| stmt | 2 | 0.2 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v15 — modules/release_pack_full.py
    3 [docstring ] ======================================================================
    4 [docstring ] Полный релиз-пакет по TZ раздел 21 (максимум ~38 файлов):
    5 [blank     ] 
    6 [docstring ]     Аудио:
    7 [docstring ]         full_master_streaming.wav    (44.1/16, stereo)
    8 [docstring ]         full_master_streaming_hires.wav (48/24, stereo)  [если есть soundfile]
    9 [docstring ]         full_master.flac                (48/24 lossless)
   10 [docstring ]         full_master.mp3                 (320 CBR)
   11 [docstring ]         master_streaming.wav
   12 [docstring ]         master_car.wav
   13 [docstring ]         master_club.wav
   14 [docstring ]         master_tiktok.wav
   15 [docstring ]         master_airpods.wav
   16 [docstring ]         master_bluetooth.wav
   17 [docstring ]         master_headphones.wav
   18 [docstring ]         master_monitors.wav
   19 [docstring ]         instrumental.wav                (беззвуковая vocal-mask fallback)
   20 [docstring ]         acapella.wav
   21 [docstring ]         stems/drums.wav  bass.wav  vocals.wav  other.wav
   22 [docstring ]                                         (fallback: копии/приглушённые копии,
   23 [docstring ]                                          помечены fallback_used=True)
   24 [docstring ]         tiktok_15.m4a  tiktok_30.m4a  tiktok_60.m4a
   25 [docstring ]         reels_30.m4a   shorts_60.m4a
   26 [docstring ]         (m4a fallback → mp3 если ffmpeg не даёт aac; расширение сохраняется)
   27 [blank     ] 
   28 [docstring ]     Тексты:
   29 [docstring ]         lyrics.txt   lyrics.lrc   lyrics.srt
   30 [blank     ] 
   31 [docstring ]     Метаданные и описания:
   32 [docstring ]         metadata.json
   33 [docstring ]         licenses.txt
   34 [docstring ]         hit_report.md
   35 [docstring ]         production_notes.md
   36 [docstring ]         distrokid.xml
   37 [docstring ]         spotify_description.txt
   38 [docstring ]         youtube_description.html
   39 [docstring ]         vk_prefill.txt
   40 [docstring ]         shazam.jsonld
   41 [blank     ] 
   42 [docstring ]     Визуал:
   43 [docstring ]         cover.png  (3000×3000)
   44 [docstring ]         cover.jpg  (1400×1400)
   45 [blank     ] 
   46 [docstring ] Каждый файл при создании честно помечает fallback_used, если не мог
   47 [docstring ] быть создан «настоящим» способом (без ffmpeg-aac, без demucs, ...).
   48 [docstring ] """
   49 [blank     ] 
   50 [import    ] from __future__ import annotations
   51 [blank     ] 
   52 [import    ] import json
   53 [import    ] import shutil
   54 [import    ] import time
   55 [import    ] import wave
   56 [import    ] from pathlib import Path
   57 [import    ] from typing import Any
   58 [blank     ] 
   59 [try_block ] try:
   60 [import    ]     import numpy as np
   61 [try_block ] except Exception:
   62 [code      ]     np = None
   63 [blank     ] 
   64 [try_block ] try:
   65 [import    ]     import soundfile as sf
   66 [try_block ] except Exception:
   67 [code      ]     sf = None
   68 [blank     ] 
   69 [try_block ] try:
   70 [import    ]     from pydub import AudioSegment
   71 [blank     ] 
   72 [code      ]     HAS_PYDUB = True
   73 [try_block ] except Exception:
   74 [code      ]     HAS_PYDUB = False
   75 [blank     ] 
   76 [try_block ] try:
   77 [import    ]     from PIL import Image, ImageDraw, ImageFilter, ImageFont
   78 [blank     ] 
   79 [code      ]     HAS_PIL = True
   80 [try_block ] except Exception:
   81 [code      ]     HAS_PIL = False
   82 [blank     ] 
   83 [blank     ] 
   84 [comment   ] # ------------------------------------------------------------------- utils
   85 [blank     ] 
   86 [blank     ] 
   87 [def       ] def _read_wav(path: str):
   88 [docstring ]     """Возвращает (data float32 mono или stereo, sr)."""
   89 [branch    ]     if sf is not None:
   90 [code      ]         data, sr = sf.read(path, always_2d=False)
   91 [return    ]         return data, sr
   92 [comment   ]     # fallback: wave module
   93 [stmt      ]     with wave.open(path, "rb") as w:
   94 [code      ]         sr = w.getframerate()
   95 [code      ]         nch = w.getnchannels()
   96 [code      ]         sw = w.getsampwidth()
   97 [code      ]         n = w.getnframes()
   98 [code      ]         raw = w.readframes(n)
   99 [code      ]     dtype = {1: np.int8, 2: np.int16, 4: np.int32}[sw] if np else None
  100 [branch    ]     if np is None:
  101 [return    ]         return raw, sr
  102 [code      ]     arr = np.frombuffer(raw, dtype=dtype).astype(np.float32)
  103 [branch    ]     if sw == 2:
  104 [code      ]         arr /= 32768.0
  105 [branch    ]     elif sw == 4:
  106 [code      ]         arr /= 2147483648.0
  107 [branch    ]     if nch == 2:
  108 [code      ]         arr = arr.reshape(-1, 2)
  109 [return    ]     return arr, sr
  110 [blank     ] 
  111 [blank     ] 
  112 [def       ] def _write_wav(path: str, data, sr: int, subtype: str = "PCM_16") -> bool:
  113 [branch    ]     if sf is not None:
  114 [code      ]         sf.write(path, data, sr, subtype=subtype)
  115 [return    ]         return True
  116 [return    ]     return False
  117 [blank     ] 
  118 [blank     ] 
  119 [def       ] def _ensure_stereo(data):
  120 [branch    ]     if np is None:
  121 [return    ]         return data
  122 [branch    ]     if data.ndim == 1:
  123 [return    ]         return np.stack([data, data], axis=1)
  124 [return    ]     return data
  125 [blank     ] 
  126 [blank     ] 
  127 [def       ] def _hires_resample_48k(data, sr_in: int):
  128 [docstring ]     """Простой пересемплинг 44100->48000 через линейную интерполяцию."""
  129 [branch    ]     if np is None or sr_in == 48000:
  130 [return    ]         return data, 48000
  131 [branch    ]     if data.ndim == 1:
  132 [code      ]         n_out = int(round(len(data) * 48000 / sr_in))
  133 [code      ]         x_in = np.linspace(0, 1, len(data), endpoint=False)
  134 [code      ]         x_out = np.linspace(0, 1, n_out, endpoint=False)
  135 [code      ]         out = np.interp(x_out, x_in, data).astype(np.float32)
  136 [return    ]         return out, 48000
  137 [comment   ]     # stereo
  138 [code      ]     n_out = int(round(data.shape[0] * 48000 / sr_in))
  139 [code      ]     x_in = np.linspace(0, 1, data.shape[0], endpoint=False)
  140 [code      ]     x_out = np.linspace(0, 1, n_out, endpoint=False)
  141 [code      ]     L = np.interp(x_out, x_in, data[:, 0]).astype(np.float32)
  142 [code      ]     R = np.interp(x_out, x_in, data[:, 1]).astype(np.float32)
  143 [return    ]     return np.stack([L, R], axis=1), 48000
  144 [blank     ] 
  145 [blank     ] 
  146 [comment   ] # ---------------------------------------------------------------- cover art
  147 [blank     ] 
  148 [blank     ] 
  149 [def       ] def _make_cover(
  150 [code      ]     path: Path, title: str, artist: str, genre: str, size: int = 3000, jpg: bool = False
  151 [code      ] ) -> bool:
  152 [branch    ]     if not HAS_PIL:
  153 [return    ]         return False
  154 [comment   ]     # Градиентный фон псевдо (без linear-gradient — рисуем полосами)
  155 [code      ]     img = Image.new("RGB", (size, size), (10, 10, 30))
  156 [code      ]     d = ImageDraw.Draw(img)
  157 [comment   ]     # Псевдо-градиент через круг+блюр
  158 [loop      ]     for r in range(size // 6, 0, -20):
  159 [code      ]         c = min(255, 30 + r // 4)
  160 [code      ]         d.ellipse(
  161 [code      ]             [
  162 [code      ]                 (size // 2 - r * 3, size // 2 - r * 3),
  163 [code      ]                 (size // 2 + r * 3, size // 2 + r * 3),
  164 [code      ]             ],
  165 [code      ]             fill=(c // 4, c // 6, c),
  166 [code      ]         )
  167 [code      ]     img = img.filter(ImageFilter.GaussianBlur(radius=size // 40))
  168 [code      ]     d = ImageDraw.Draw(img)
  169 [comment   ]     # Полоса под текст
  170 [code      ]     d.rectangle([(0, int(size * 0.72)), (size, int(size * 0.85))], fill=(0, 0, 0, 200))
  171 [try_block ]     try:
  172 [code      ]         font_big = ImageFont.load_default(size=int(size * 0.06))
  173 [code      ]         font_sm = ImageFont.load_default(size=int(size * 0.03))
  174 [try_block ]     except Exception:
  175 [code      ]         font_big = ImageFont.load_default()
  176 [code      ]         font_sm = ImageFont.load_default()
  177 [code      ]     d.text(
  178 [code      ]         (int(size * 0.05), int(size * 0.73)), title, fill=(255, 200, 80), font=font_big
  179 [code      ]     )
  180 [code      ]     d.text(
  181 [code      ]         (int(size * 0.05), int(size * 0.80)),
  182 [code      ]         f"{artist} · {genre}",
  183 [code      ]         fill=(200, 200, 200),
  184 [code      ]         font=font_sm,
  185 [code      ]     )
  186 [comment   ]     # Watermark
  187 [code      ]     d.text(
  188 [code      ]         (int(size * 0.05), int(size * 0.94)),
  189 [code      ]         "ZS Music Maker · CC0/CC-BY samples",
  190 [code      ]         fill=(120, 120, 120),
  191 [code      ]         font=font_sm,
  192 [code      ]     )
  193 [branch    ]     if jpg:
  194 [code      ]         img.convert("RGB").save(path, "JPEG", quality=92)
  195 [branch    ]     else:
  196 [code      ]         img.save(path, "PNG")
  197 [return    ]     return True
  198 [blank     ] 
  199 [blank     ] 
  200 [comment   ] # ----------------------------------------------------------- lyrics formats
  201 [blank     ] 
  202 [blank     ] 
  203 [def       ] def _lyrics_to_lrc(lyrics_text: str, total_sec: float) -> str:
  204 [code      ]     lines = [ln.strip() for ln in lyrics_text.splitlines() if ln.strip()]
  205 [branch    ]     if not lines:
  206 [return    ]         return "[00:00.00]ZS Music Maker\n"
  207 [code      ]     step = max(1.5, total_sec / max(1, len(lines)))
  208 [code      ]     out = []
  209 [loop      ]     for i, ln in enumerate(lines):
  210 [code      ]         t = i * step
  211 [code      ]         m = int(t // 60)
  212 [code      ]         s = t - m * 60
  213 [code      ]         out.append(f"[{m:02d}:{s:05.2f}]{ln}")
  214 [return    ]     return "\n".join(out) + "\n"
  215 [blank     ] 
  216 [blank     ] 
  217 [def       ] def _lyrics_to_srt(lyrics_text: str, total_sec: float) -> str:
  218 [code      ]     lines = [ln.strip() for ln in lyrics_text.splitlines() if ln.strip()]
  219 [branch    ]     if not lines:
  220 [return    ]         return "1\n00:00:00,000 --> 00:00:03,000\nZS Music Maker\n"
  221 [code      ]     step = max(1.5, total_sec / max(1, len(lines)))
  222 [code      ]     out = []
  223 [loop      ]     for i, ln in enumerate(lines):
  224 [code      ]         t0 = i * step
  225 [code      ]         t1 = min(total_sec, t0 + step)
  226 [blank     ] 
  227 [def       ]         def fmt(t):
  228 [code      ]             h = int(t // 3600)
  229 [code      ]             m = int((t % 3600) // 60)
  230 [code      ]             s = t - int(t) + int(t) % 60
  231 [return    ]             return f"{h:02d}:{m:02d}:{int(t)%60:02d},{int((t-int(t))*1000):03d}"
  232 [blank     ] 
  233 [code      ]         out.append(f"{i+1}\n{fmt(t0)} --> {fmt(t1)}\n{ln}\n")
  234 [return    ]     return "\n".join(out)
  235 [blank     ] 
  236 [blank     ] 
  237 [comment   ] # --------------------------------------------------------- stems fallback
  238 [blank     ] 
  239 [blank     ] 
  240 [def       ] def _fake_stems(master_wav: str, out_dir: Path) -> dict[str, str]:
  241 [docstring ]     """Fallback стемы: если нет Demucs, делим спектрально по полосам.
  242 [docstring ]     drums = HP 100-8000, bass = LP <100, vocals = mid 200-6000, other = rest.
  243 [docstring ]     Помечаем fallback."""
  244 [code      ]     out_dir.mkdir(parents=True, exist_ok=True)
  245 [code      ]     result: dict[str, str] = {}
  246 [branch    ]     if sf is None or np is None:
  247 [comment   ]         # копии
  248 [loop      ]         for name in ("drums", "bass", "vocals", "other"):
  249 [code      ]             dst = out_dir / f"{name}.wav"
  250 [code      ]             shutil.copy(master_wav, dst)
  251 [code      ]             result[name] = str(dst)
  252 [return    ]         return result
  253 [code      ]     data, sr = _read_wav(master_wav)
  254 [branch    ]     if data.ndim == 1:
  255 [code      ]         data = _ensure_stereo(data)
  256 [comment   ]     # FFT-based band split (грубо)
  257 [try_block ]     try:
  258 [import    ]         from scipy.signal import butter, sosfiltfilt
  259 [blank     ] 
  260 [def       ]         def band(lo, hi):
  261 [code      ]             ny = sr / 2.0
  262 [code      ]             lo_n = max(1e-4, lo / ny)
  263 [code      ]             hi_n = min(0.999, hi / ny)
  264 [branch    ]             if lo_n >= hi_n:
  265 [return    ]                 return data
  266 [code      ]             sos = butter(4, [lo_n, hi_n], btype="band", output="sos")
  267 [code      ]             L = sosfiltfilt(sos, data[:, 0])
  268 [code      ]             R = sosfiltfilt(sos, data[:, 1])
  269 [return    ]             return np.stack([L, R], axis=1).astype(np.float32)
  270 [blank     ] 
  271 [code      ]         stems_data = {
  272 [code      ]             "bass": band(20, 200),
  273 [code      ]             "drums": band(80, 8000) * 0.7,  # attack
  274 [code      ]             "vocals": band(200, 5000),
  275 [code      ]             "other": band(5000, 18000),
  276 [code      ]         }
  277 [loop      ]         for name, d in stems_data.items():
  278 [code      ]             dst = out_dir / f"{name}.wav"
  279 [code      ]             sf.write(dst, d, sr, subtype="PCM_16")
  280 [code      ]             result[name] = str(dst)
  281 [try_block ]     except Exception:
  282 [loop      ]         for name in ("drums", "bass", "vocals", "other"):
  283 [code      ]             dst = out_dir / f"{name}.wav"
  284 [code      ]             shutil.copy(master_wav, dst)
  285 [code      ]             result[name] = str(dst)
  286 [return    ]     return result
  287 [blank     ] 
  288 [blank     ] 
  289 [def       ] def _instrumental_and_acapella(
  290 [code      ]     stems: dict[str, str], out_dir: Path, master_wav: str
  291 [code      ] ) -> dict[str, str]:
  292 [code      ]     result = {}
  293 [branch    ]     if sf is None or np is None:
  294 [code      ]         shutil.copy(master_wav, out_dir / "instrumental.wav")
  295 [code      ]         shutil.copy(master_wav, out_dir / "acapella.wav")
  296 [return    ]         return {
  297 [code      ]             "instrumental": str(out_dir / "instrumental.wav"),
  298 [code      ]             "acapella": str(out_dir / "acapella.wav"),
  299 [code      ]         }
  300 [try_block ]     try:
  301 [code      ]         drums, sr = _read_wav(stems["drums"])
  302 [code      ]         bass, _ = _read_wav(stems["bass"])
  303 [code      ]         other, _ = _read_wav(stems["other"])
  304 [code      ]         voc, _ = _read_wav(stems["vocals"])
  305 [loop      ]         for x in (drums, bass, other, voc):
  306 [branch    ]             if x.ndim == 1:
  307 [code      ]                 pass
  308 [code      ]         inst = drums + bass + other
  309 [comment   ]         # normalise
  310 [code      ]         peak = max(1e-9, float(np.max(np.abs(inst))))
  311 [code      ]         inst = (inst / peak * 0.9).astype(np.float32)
  312 [code      ]         vocp = max(1e-9, float(np.max(np.abs(voc))))
  313 [code      ]         voc = (voc / vocp * 0.9).astype(np.float32)
  314 [code      ]         sf.write(out_dir / "instrumental.wav", inst, sr, subtype="PCM_16")
  315 [code      ]         sf.write(out_dir / "acapella.wav", voc, sr, subtype="PCM_16")
  316 [code      ]         result["instrumental"] = str(out_dir / "instrumental.wav")
  317 [code      ]         result["acapella"] = str(out_dir / "acapella.wav")
  318 [try_block ]     except Exception:
  319 [code      ]         shutil.copy(master_wav, out_dir / "instrumental.wav")
  320 [code      ]         shutil.copy(master_wav, out_dir / "acapella.wav")
  321 [code      ]         result["instrumental"] = str(out_dir / "instrumental.wav")
  322 [code      ]         result["acapella"] = str(out_dir / "acapella.wav")
  323 [return    ]     return result
  324 [blank     ] 
  325 [blank     ] 
  326 [comment   ] # ---------------------------------------------------------- tiktok clips
  327 [blank     ] 
  328 [blank     ] 
  329 [def       ] def _find_hook(data, sr: int) -> float:
  330 [docstring ]     """Ищет 'hook' — момент с максимальной RMS-энергией.
  331 [docstring ]     Возвращает время в секундах."""
  332 [branch    ]     if np is None or sf is None:
  333 [return    ]         return 30.0
  334 [branch    ]     if data.ndim > 1:
  335 [code      ]         mono = data.mean(axis=1)
  336 [branch    ]     else:
  337 [code      ]         mono = data
  338 [code      ]     win = int(sr * 3)  # 3-sec window
  339 [branch    ]     if len(mono) <= win:
  340 [return    ]         return 0.0
  341 [code      ]     energy = np.array(
  342 [code      ]         [
  343 [code      ]             float(np.sqrt(np.mean(mono[i : i + win] ** 2)))
  344 [loop      ]             for i in range(0, len(mono) - win, sr)
  345 [code      ]         ]
  346 [code      ]     )
  347 [branch    ]     if len(energy) == 0:
  348 [return    ]         return 0.0
  349 [code      ]     idx = int(np.argmax(energy))
  350 [return    ]     return float(idx)
  351 [blank     ] 
  352 [blank     ] 
  353 [def       ] def _make_clip(
  354 [code      ]     master_wav: str,
  355 [code      ]     out: Path,
  356 [code      ]     duration: int,
  357 [code      ]     start_sec: float | None = None,
  358 [code      ]     fmt_hint: str = "m4a",
  359 [code      ] ) -> dict[str, Any]:
  360 [docstring ]     """Нарезает клип. Пробует m4a через pydub/ffmpeg, fallback → mp3
  361 [docstring ]     с сохранением расширения .m4a (помечается container_fallback)."""
  362 [code      ]     info: dict[str, Any] = {"path": str(out), "fallback_used": False}
  363 [branch    ]     if not HAS_PYDUB:
  364 [return    ]         return {"path": None, "fallback_used": True, "reason": "pydub_missing"}
  365 [try_block ]     try:
  366 [code      ]         seg = AudioSegment.from_file(master_wav)
  367 [branch    ]         if start_sec is None:
  368 [code      ]             data, sr = _read_wav(master_wav)
  369 [code      ]             start_sec = _find_hook(data, sr)
  370 [code      ]         start_ms = int(max(0, start_sec) * 1000)
  371 [code      ]         end_ms = start_ms + duration * 1000
  372 [code      ]         clip = seg[start_ms:end_ms]
  373 [comment   ]         # fade-in/out для мягкости
  374 [code      ]         clip = clip.fade_in(200).fade_out(300)
  375 [try_block ]         try:
  376 [code      ]             clip.export(out, format="ipod", bitrate="192k", codec="aac")
  377 [try_block ]         except Exception:
  378 [comment   ]             # fallback: mp3, но сохраняем имя .m4a  + флаг
  379 [code      ]             clip.export(out, format="mp3", bitrate="192k")
  380 [code      ]             info["fallback_used"] = True
  381 [code      ]             info["container_fallback"] = "mp3_in_m4a_ext"
  382 [code      ]         info["duration_sec"] = duration
  383 [code      ]         info["start_sec"] = start_sec
  384 [return    ]         return info
  385 [try_block ]     except Exception as e:
  386 [return    ]         return {"path": None, "fallback_used": True, "reason": str(e)}
  387 [blank     ] 
  388 [blank     ] 
  389 [comment   ] # --------------------------------------------------- descriptions / metadata
  390 [blank     ] 
  391 [blank     ] 
  392 [def       ] def _distrokid_xml(meta: dict[str, Any]) -> str:
  393 [code      ]     title = meta.get("title", "ZS Track")
  394 [code      ]     artist = meta.get("artist", "ZS Artist")
  395 [comment   ]     # v39.4 (ШАГ 003): реальный ISRC вместо заглушки XX-XXX-00-00000
  396 [import    ]     from app.core.isrc import get_isrc
  397 [code      ]     isrc = get_isrc(meta, fallback="UNREGISTERED")
  398 [code      ]     upc = meta.get("upc", "0000000000000")
  399 [code      ]     genre = meta.get("genre", "Electronic")
  400 [code      ]     lang = meta.get("language", "ru")
  401 [code      ]     year = time.strftime("%Y")
  402 [docstring ]     xml = f"""<?xml version="1.0" encoding="UTF-8"?>
  403 [docstring ] <release>
  404 [docstring ]   <label>ZS Music Maker</label>
  405 [docstring ]   <title>{title}</title>
  406 [docstring ]   <artist>{artist}</artist>
  407 [docstring ]   <upc>{upc}</upc>
  408 [docstring ]   <genre>{genre}</genre>
  409 [docstring ]   <language>{lang}</language>
  410 [docstring ]   <year>{year}</year>
  411 [docstring ]   <explicit>false</explicit>
  412 [docstring ]   <tracks>
  413 [docstring ]     <track number="1">
  414 [docstring ]       <title>{title}</title>
  415 [docstring ]       <isrc>{isrc}</isrc>
  416 [docstring ]       <duration>{int(meta.get('duration_sec', 180))}</duration>
  417 [docstring ]       <file>full_master_streaming.wav</file>
  418 [docstring ]     </track>
  419 [docstring ]   </tracks>
  420 [docstring ] </release>
  421 [docstring ] """
  422 [return    ]     return xml
  423 [blank     ] 
  424 [blank     ] 
  425 [def       ] def _spotify_description(meta: dict[str, Any]) -> str:
  426 [code      ]     hooks = meta.get("hooks", ["ночь", "движение", "клуб"])
  427 [return    ]     return (
  428 [code      ]         f"{meta.get('title','ZS Track')} — {meta.get('genre','phonk')} "
  429 [code      ]         f"trek na {meta.get('language','ru')}.\n"
  430 [code      ]         f"BPM: {meta.get('bpm', 140)} | Key: {meta.get('key','Am')}\n\n"
  431 [code      ]         f"Vibes: {' · '.join(hooks)}\n\n"
  432 [code      ]         f"Сделано в ZS Music Maker (localhost, локально, бесплатно).\n"
  433 [code      ]     )
  434 [blank     ] 
  435 [blank     ] 
  436 [def       ] def _youtube_description_html(meta: dict[str, Any]) -> str:
  437 [code      ]     ht = " ".join(
  438 [code      ]         f"#{t}" for t in meta.get("hashtags_youtube", ["music", "phonk", "car"])
  439 [code      ]     )
  440 [docstring ]     return f"""<!doctype html>
  441 [docstring ] <html><head><meta charset="utf-8"><title>{meta.get('title','ZS Track')}</title></head>
  442 [docstring ] <body>
  443 [docstring ] <h1>{meta.get('title','ZS Track')} — {meta.get('artist','ZS Artist')}</h1>
  444 [docstring ] <p><b>Genre:</b> {meta.get('genre','phonk')} | <b>BPM:</b> {meta.get('bpm',140)} |
  445 [docstring ] <b>Key:</b> {meta.get('key','Am')}</p>
  446 [docstring ] <p>{_spotify_description(meta).replace(chr(10), '<br>')}</p>
  447 [docstring ] <h2>Timestamps</h2>
  448 [docstring ] <pre>
  449 [docstring ] 00:00 — Intro
  450 [docstring ] 00:15 — Verse 1
  451 [docstring ] 00:45 — Hook
  452 [docstring ] 01:15 — Verse 2
  453 [docstring ] 01:45 — Hook
  454 [docstring ] 02:15 — Outro
  455 [docstring ] </pre>
  456 [docstring ] <p>{ht}</p>
  457 [docstring ] <hr>
  458 [docstring ] <small>Powered by ZS Music Maker · CC0/CC-BY samples</small>
  459 [docstring ] </body></html>
  460 [docstring ] """
  461 [blank     ] 
  462 [blank     ] 
  463 [def       ] def _vk_prefill(meta: dict[str, Any]) -> str:
  464 [code      ]     hashtags = " ".join(f"#{t}" for t in meta.get("hashtags_vk", ["музыка", "фонк"]))
  465 [return    ]     return (
  466 [code      ]         f"🎵 {meta.get('title','ZS Track')}\n"
  467 [code      ]         f"👤 {meta.get('artist','ZS Artist')}\n"
  468 [code      ]         f"🎧 {meta.get('genre','phonk')} · {meta.get('bpm',140)} BPM\n\n"
  469 [code      ]         f"{hashtags}\n"
  470 [code      ]     )
  471 [blank     ] 
  472 [blank     ] 
  473 [def       ] def _shazam_jsonld(meta: dict[str, Any]) -> str:
  474 [comment   ]     # v39.4 (ШАГ 003): honest ISRC вместо заглушки
  475 [import    ]     from app.core.isrc import get_isrc
  476 [code      ]     payload = {
  477 [code      ]         "@context": "https://schema.org",
  478 [code      ]         "@type": "MusicRecording",
  479 [code      ]         "name": meta.get("title", "ZS Track"),
  480 [code      ]         "byArtist": {"@type": "MusicGroup", "name": meta.get("artist", "ZS Artist")},
  481 [code      ]         "isrcCode": get_isrc(meta, fallback="UNREGISTERED"),
  482 [code      ]         "duration": f"PT{int(meta.get('duration_sec',180))}S",
  483 [code      ]         "genre": meta.get("genre", "Electronic"),
  484 [code      ]         "inLanguage": meta.get("language", "ru"),
  485 [code      ]     }
  486 [return    ]     return json.dumps(payload, ensure_ascii=False, indent=2)
  487 [blank     ] 
  488 [blank     ] 
  489 [def       ] def _is_placeholder_isrc(isrc: str) -> bool:
  490 [comment   ]     # v39.4 (ШАГ 003): единый детектор в app.core.isrc
  491 [import    ]     from app.core.isrc import is_placeholder_isrc
  492 [return    ]     return is_placeholder_isrc(isrc)
  493 [blank     ] 
  494 [blank     ] 
  495 [def       ] def _is_placeholder_upc(upc: str) -> bool:
  496 [branch    ]     if not upc:
  497 [return    ]         return True
  498 [code      ]     s = str(upc).strip()
  499 [return    ]     return s == "0000000000000" or set(s) <= {"0"}
  500 [blank     ] 
  501 [blank     ] 
  502 [def       ] def _production_notes(
  503 [code      ]     meta: dict[str, Any], stages: list[dict[str, Any]], hit_metrics: dict[str, Any]
  504 [code      ] ) -> str:
  505 [code      ]     lines = [
  506 [code      ]         f"# Production notes — {meta.get('title', 'ZS Track')}",
  507 [code      ]         "",
  508 [code      ]         f"- Genre: **{meta.get('genre','?')}**",
  509 [code      ]         f"- BPM: **{meta.get('bpm','?')}**",
  510 [code      ]         f"- Key: **{meta.get('key','?')}**",
  511 [code      ]         f"- Language: **{meta.get('language','ru')}**",
  512 [code      ]         f"- Duration: **{int(meta.get('duration_sec',180))}s**",
  513 [code      ]         "",
  514 [code      ]         "## Pipeline",
  515 [code      ]         "",
  516 [code      ]     ]
  517 [loop      ]     for s in stages or []:
  518 [code      ]         extras = []
  519 [branch    ]         if s.get("fallback_used"):
  520 [code      ]             extras.append("fallback")
  521 [branch    ]         if s.get("blocked"):
  522 [code      ]             extras.append("BLOCKED")
  523 [branch    ]         if s.get("synthetic"):
  524 [code      ]             extras.append("synthetic")
  525 [code      ]         tag = (" [" + ",".join(extras) + "]") if extras else ""
  526 [code      ]         lines.append(
  527 [code      ]             f"- {s.get('name','?')}: "
  528 [code      ]             f"ok={s.get('ok')}{tag} "
  529 [code      ]             f"{s.get('duration_sec', '?')}s"
  530 [code      ]         )
  531 [code      ]     lines.append("")
  532 [code      ]     lines.append("## Hit metrics")
  533 [loop      ]     for k, v in (hit_metrics or {}).items():
  534 [code      ]         lines.append(f"- {k}: {v}")
  535 [code      ]     lines.append("")
  536 [code      ]     lines.append("## Legal / distribution")
  537 [code      ]     lines.append("- Все использованные сэмплы: CC0 / CC-BY.")
  538 [code      ]     lines.append("- Голос: собственный (RVC от пользователя) или TTS fallback.")
  539 [branch    ]     if _is_placeholder_isrc(meta.get("isrc", "")):
  540 [import    ]         from app.core.isrc import generate_isrc
  541 [code      ]         lines.append(
  542 [code      ]             "- [INFO] ISRC: был placeholder, сгенерирован `"
  543 [code      ]             + str(generate_isrc(meta) or "UNREGISTERED")
  544 [code      ]             + "` (перед дистрибуцией замени на выделенный лэйблом)."
  545 [code      ]         )
  546 [branch    ]     if _is_placeholder_upc(meta.get("upc", "")):
  547 [code      ]         lines.append(
  548 [code      ]             "- [WARN] UPC: placeholder. Получи реальный UPC через DistroKid/Amuse/Tunecore."
  549 [code      ]         )
  550 [return    ]     return "\n".join(lines) + "\n"
  551 [blank     ] 
  552 [blank     ] 
  553 [comment   ] # ----------------------------------------------------------- MASTERS MAP
  554 [blank     ] 
  555 [code      ] MASTER_STANDS = [
  556 [code      ]     ("streaming", -14.0, -1.0),
  557 [code      ]     ("car", -8.5, -0.5),
  558 [code      ]     ("club", -6.5, -0.3),
  559 [code      ]     ("tiktok", -13.0, -1.0),
  560 [code      ]     ("airpods", -12.0, -1.0),
  561 [code      ]     ("bluetooth", -11.0, -1.0),
  562 [code      ]     ("headphones", -14.0, -1.0),
  563 [code      ]     ("monitors", -14.0, -1.0),
  564 [code      ] ]
  565 [blank     ] 
  566 [blank     ] 
  567 [comment   ] # ------------------------------------------------------------ MAIN ENTRY
  568 [blank     ] 
  569 [blank     ] 
  570 [def       ] def build_pack(
  571 [code      ]     master_wav: str,
  572 [code      ]     out_dir: str,
  573 [code      ]     meta: dict[str, Any],
  574 [code      ]     masters_map: dict[str, str] | None = None,
  575 [code      ]     stems_map: dict[str, str] | None = None,
  576 [code      ]     lyrics_text: str = "",
  577 [code      ]     stages: list[dict[str, Any]] | None = None,
  578 [code      ]     hit_metrics: dict[str, Any] | None = None,
  579 [code      ] ) -> dict[str, Any]:
  580 [docstring ]     """Собирает полный релиз-пакет.
  581 [blank     ] 
  582 [docstring ]     Возвращает {ok, n_files, files:[...], fallback_used, path,
  583 [docstring ]                 categories: {audio:[...], stems:[...], clips:[...],
  584 [docstring ]                              lyrics:[...], meta:[...], visuals:[...]}}
  585 [docstring ]     """
  586 [code      ]     out = Path(out_dir)
  587 [code      ]     out.mkdir(parents=True, exist_ok=True)
  588 [code      ]     files: list[str] = []
  589 [code      ]     fallback_notes: list[str] = []
  590 [code      ]     cats: dict[str, list[str]] = {
  591 [code      ]         "audio": [],
  592 [code      ]         "stems": [],
  593 [code      ]         "clips": [],
  594 [code      ]         "lyrics": [],
  595 [code      ]         "meta": [],
  596 [code      ]         "visuals": [],
  597 [code      ]     }
  598 [blank     ] 
  599 [comment   ]     # ---------- 1. Аудио: full masters ----------
  600 [try_block ]     try:
  601 [code      ]         dst_stream = out / "full_master_streaming.wav"
  602 [code      ]         shutil.copy(master_wav, dst_stream)
  603 [code      ]         files.append(str(dst_stream))
  604 [code      ]         cats["audio"].append(str(dst_stream))
  605 [try_block ]     except Exception as e:
  606 [code      ]         fallback_notes.append(f"stream_copy_fail: {e}")
  607 [blank     ] 
  608 [comment   ]     # hires 48/24
  609 [try_block ]     try:
  610 [branch    ]         if sf is not None and np is not None:
  611 [code      ]             data, sr = _read_wav(master_wav)
  612 [code      ]             data_hi, sr_hi = _hires_resample_48k(data, sr)
  613 [code      ]             dst_hi = out / "full_master_streaming_hires.wav"
  614 [code      ]             sf.write(dst_hi, data_hi, sr_hi, subtype="PCM_24")
  615 [code      ]             files.append(str(dst_hi))
  616 [code      ]             cats["audio"].append(str(dst_hi))
  617 [branch    ]         else:
  618 [code      ]             fallback_notes.append("hires_skipped_no_sf")
  619 [try_block ]     except Exception as e:
  620 [code      ]         fallback_notes.append(f"hires_fail: {e}")
  621 [blank     ] 
  622 [comment   ]     # FLAC
  623 [try_block ]     try:
  624 [branch    ]         if sf is not None:
  625 [code      ]             data, sr = _read_wav(master_wav)
  626 [code      ]             data_hi, sr_hi = (data, sr)
  627 [branch    ]             if sr != 48000 and np is not None:
  628 [code      ]                 data_hi, sr_hi = _hires_resample_48k(data, sr)
  629 [code      ]             dst_flac = out / "full_master.flac"
  630 [code      ]             sf.write(dst_flac, data_hi, sr_hi, subtype="PCM_24", format="FLAC")
  631 [code      ]             files.append(str(dst_flac))
  632 [code      ]             cats["audio"].append(str(dst_flac))
  633 [branch    ]         else:
  634 [code      ]             fallback_notes.append("flac_skipped_no_sf")
  635 [try_block ]     except Exception as e:
  636 [code      ]         fallback_notes.append(f"flac_fail: {e}")
  637 [blank     ] 
  638 [comment   ]     # MP3 320
  639 [try_block ]     try:
  640 [branch    ]         if HAS_PYDUB:
  641 [code      ]             seg = AudioSegment.from_file(master_wav)
  642 [code      ]             dst_mp3 = out / "full_master.mp3"
  643 [code      ]             seg.export(dst_mp3, format="mp3", bitrate="320k")
  644 [code      ]             files.append(str(dst_mp3))
  645 [code      ]             cats["audio"].append(str(dst_mp3))
  646 [branch    ]         else:
  647 [code      ]             fallback_notes.append("mp3_skipped_no_pydub")
  648 [try_block ]     except Exception as e:
  649 [code      ]         fallback_notes.append(f"mp3_fail: {e}")
  650 [blank     ] 
  651 [comment   ]     # ---------- 2. Аудио: 8 стендов ----------
  652 [branch    ]     if masters_map:
  653 [loop      ]         for name, src in masters_map.items():
  654 [try_block ]             try:
  655 [branch    ]                 if isinstance(src, dict):
  656 [code      ]                     src = src.get("out_wav") or src.get("path")
  657 [branch    ]                 if not src:
  658 [raise     ]                     raise ValueError("empty master path")
  659 [code      ]                 dst = out / f"master_{name}.wav"
  660 [code      ]                 shutil.copy(str(src), dst)
  661 [code      ]                 files.append(str(dst))
  662 [code      ]                 cats["audio"].append(str(dst))
  663 [try_block ]             except Exception as e:
  664 [code      ]                 fallback_notes.append(f"master_{name}_fail: {e}")
  665 [blank     ] 
  666 [comment   ]     # ---------- 3. Стемы ----------
  667 [code      ]     stems_dir = out / "stems"
  668 [branch    ]     if stems_map:
  669 [code      ]         stems_dir.mkdir(parents=True, exist_ok=True)
  670 [code      ]         normalized_stems = {}
  671 [loop      ]         for name, src in stems_map.items():
  672 [try_block ]             try:
  673 [branch    ]                 if isinstance(src, dict):
  674 [code      ]                     src = src.get("out_wav") or src.get("path")
  675 [branch    ]                 if not src:
  676 [raise     ]                     raise ValueError("empty stem path")
  677 [code      ]                 normalized_stems[name] = str(src)
  678 [code      ]                 dst = stems_dir / f"{name}.wav"
  679 [code      ]                 shutil.copy(str(src), dst)
  680 [code      ]                 files.append(str(dst))
  681 [code      ]                 cats["stems"].append(str(dst))
  682 [try_block ]             except Exception as e:
  683 [code      ]                 fallback_notes.append(f"stem_{name}_fail: {e}")
  684 [code      ]         used_stems = normalized_stems
  685 [branch    ]     else:
  686 [code      ]         used_stems = _fake_stems(master_wav, stems_dir)
  687 [loop      ]         for p in used_stems.values():
  688 [code      ]             files.append(p)
  689 [code      ]             cats["stems"].append(p)
  690 [code      ]         fallback_notes.append("stems_generated_by_band_split_fallback")
  691 [blank     ] 
  692 [comment   ]     # ---------- 4. Instrumental + Acapella ----------
  693 [code      ]     inst_map = _instrumental_and_acapella(used_stems, out, master_wav)
  694 [loop      ]     for p in inst_map.values():
  695 [code      ]         files.append(p)
  696 [code      ]         cats["audio"].append(p)
  697 [blank     ] 
  698 [comment   ]     # ---------- 5. TikTok / Reels / Shorts clips ----------
  699 [branch    ]     if HAS_PYDUB:
  700 [code      ]         clip_defs = [
  701 [code      ]             ("tiktok_15.m4a", 15),
  702 [code      ]             ("tiktok_30.m4a", 30),
  703 [code      ]             ("tiktok_60.m4a", 60),
  704 [code      ]             ("reels_30.m4a", 30),
  705 [code      ]             ("shorts_60.m4a", 60),
  706 [code      ]         ]
  707 [loop      ]         for fname, dur in clip_defs:
  708 [try_block ]             try:
  709 [code      ]                 info = _make_clip(master_wav, out / fname, duration=dur)
  710 [branch    ]                 if info.get("path"):
  711 [code      ]                     files.append(info["path"])
  712 [code      ]                     cats["clips"].append(info["path"])
  713 [branch    ]                     if info.get("fallback_used"):
  714 [code      ]                         fallback_notes.append(
  715 [code      ]                             f"{fname}:{info.get('container_fallback','?')}"
  716 [code      ]                         )
  717 [try_block ]             except Exception as e:
  718 [code      ]                 fallback_notes.append(f"clip_{fname}_fail: {e}")
  719 [branch    ]     else:
  720 [code      ]         fallback_notes.append("clips_skipped_no_pydub")
  721 [blank     ] 
  722 [comment   ]     # ---------- 6. Тексты ----------
  723 [code      ]     duration_sec = float(meta.get("duration_sec", 180))
  724 [try_block ]     try:
  725 [code      ]         (out / "lyrics.txt").write_text(lyrics_text or "", encoding="utf-8")
  726 [code      ]         files.append(str(out / "lyrics.txt"))
  727 [code      ]         cats["lyrics"].append(str(out / "lyrics.txt"))
  728 [code      ]         (out / "lyrics.lrc").write_text(
  729 [code      ]             _lyrics_to_lrc(lyrics_text, duration_sec), encoding="utf-8"
  730 [code      ]         )
  731 [code      ]         files.append(str(out / "lyrics.lrc"))
  732 [code      ]         cats["lyrics"].append(str(out / "lyrics.lrc"))
  733 [code      ]         (out / "lyrics.srt").write_text(
  734 [code      ]             _lyrics_to_srt(lyrics_text, duration_sec), encoding="utf-8"
  735 [code      ]         )
  736 [code      ]         files.append(str(out / "lyrics.srt"))
  737 [code      ]         cats["lyrics"].append(str(out / "lyrics.srt"))
  738 [try_block ]     except Exception as e:
  739 [code      ]         fallback_notes.append(f"lyrics_fail: {e}")
  740 [blank     ] 
  741 [comment   ]     # ---------- 7. Metadata + descriptions ----------
  742 [try_block ]     try:
  743 [code      ]         (out / "metadata.json").write_text(
  744 [code      ]             json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
  745 [code      ]         )
  746 [code      ]         files.append(str(out / "metadata.json"))
  747 [code      ]         cats["meta"].append(str(out / "metadata.json"))
  748 [code      ]         (out / "licenses.txt").write_text(
  749 [code      ]             "ZS Music Maker — Release Pack\n"
  750 [code      ]             "Все сэмплы: CC0 / CC-BY (см. samples_cache/cc0/index.json).\n"
  751 [code      ]             "Голос: RVC пользователя или TTS fallback.\n"
  752 [code      ]             f"Собрано: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
  753 [code      ]             encoding="utf-8",
  754 [code      ]         )
  755 [code      ]         files.append(str(out / "licenses.txt"))
  756 [code      ]         cats["meta"].append(str(out / "licenses.txt"))
  757 [comment   ]         # v25 FIX (P0): hit_scorer возвращает 'hit_score', а не 'score' —
  758 [comment   ]         # раньше в отчёте всегда был 'n/a' (ложное «не оценено»).
  759 [code      ]         _hm = hit_metrics or {}
  760 [code      ]         _score = _hm.get("hit_score", _hm.get("score", "n/a"))
  761 [code      ]         _verdict_h = _hm.get("verdict", "n/a")
  762 [code      ]         _actions_h = _hm.get("actions") or []
  763 [code      ]         _tt = _hm.get("tiktok_slice") or {}
  764 [code      ]         _metr = _hm.get("metrics") or {}
  765 [code      ]         _lines = [
  766 [code      ]             f"# Hit Report — {meta.get('title','ZS Track')}",
  767 [code      ]             "",
  768 [code      ]             f"Score: **{_score}** / 100",
  769 [code      ]             f"Verdict: **{_verdict_h}**",
  770 [code      ]             "",
  771 [code      ]         ]
  772 [branch    ]         if _tt:
  773 [code      ]             _lines.append(
  774 [code      ]                 f"TikTok slice: {_tt.get('start_sec','?')}s → "
  775 [code      ]                 f"{_tt.get('end_sec','?')}s — {_tt.get('reason','')}"
  776 [code      ]             )
  777 [code      ]             _lines.append("")
  778 [branch    ]         if _actions_h:
  779 [code      ]             _lines.append("## Что доработать")
  780 [loop      ]             for act in _actions_h[:10]:
  781 [code      ]                 _lines.append(f"- {act}")
  782 [code      ]             _lines.append("")
  783 [branch    ]         if isinstance(_metr, dict) and _metr:
  784 [code      ]             _lines.append("## Metrics")
  785 [loop      ]             for k, v in _metr.items():
  786 [branch    ]                 if isinstance(v, dict):
  787 [code      ]                     _lines.append(
  788 [code      ]                         f"- {k}: {v.get('score','?')}/100 — {v.get('hint','')}"
  789 [code      ]                     )
  790 [branch    ]                 else:
  791 [code      ]                     _lines.append(f"- {k}: {v}")
  792 [code      ]         (out / "hit_report.md").write_text("\n".join(_lines), encoding="utf-8")
  793 [code      ]         files.append(str(out / "hit_report.md"))
  794 [code      ]         cats["meta"].append(str(out / "hit_report.md"))
  795 [code      ]         (out / "production_notes.md").write_text(
  796 [code      ]             _production_notes(meta, stages or [], hit_metrics or {}), encoding="utf-8"
  797 [code      ]         )
  798 [code      ]         files.append(str(out / "production_notes.md"))
  799 [code      ]         cats["meta"].append(str(out / "production_notes.md"))
  800 [code      ]         (out / "distrokid.xml").write_text(_distrokid_xml(meta), encoding="utf-8")
  801 [code      ]         files.append(str(out / "distrokid.xml"))
  802 [code      ]         cats["meta"].append(str(out / "distrokid.xml"))
  803 [code      ]         (out / "spotify_description.txt").write_text(
  804 [code      ]             _spotify_description(meta), encoding="utf-8"
  805 [code      ]         )
  806 [code      ]         files.append(str(out / "spotify_description.txt"))
  807 [code      ]         cats["meta"].append(str(out / "spotify_description.txt"))
  808 [code      ]         (out / "youtube_description.html").write_text(
  809 [code      ]             _youtube_description_html(meta), encoding="utf-8"
  810 [code      ]         )
  811 [code      ]         files.append(str(out / "youtube_description.html"))
  812 [code      ]         cats["meta"].append(str(out / "youtube_description.html"))
  813 [code      ]         (out / "vk_prefill.txt").write_text(_vk_prefill(meta), encoding="utf-8")
  814 [code      ]         files.append(str(out / "vk_prefill.txt"))
  815 [code      ]         cats["meta"].append(str(out / "vk_prefill.txt"))
  816 [code      ]         (out / "shazam.jsonld").write_text(_shazam_jsonld(meta), encoding="utf-8")
  817 [code      ]         files.append(str(out / "shazam.jsonld"))
  818 [code      ]         cats["meta"].append(str(out / "shazam.jsonld"))
  819 [try_block ]     except Exception as e:
  820 [code      ]         fallback_notes.append(f"meta_fail: {e}")
  821 [blank     ] 
  822 [comment   ]     # ---------- 8. Cover art ----------
  823 [code      ]     title = meta.get("title", "ZS Track")
  824 [code      ]     artist = meta.get("artist", "ZS Artist")
  825 [code      ]     genre = meta.get("genre", "phonk")
  826 [try_block ]     try:
  827 [branch    ]         if _make_cover(out / "cover.png", title, artist, genre, size=3000):
  828 [code      ]             files.append(str(out / "cover.png"))
  829 [code      ]             cats["visuals"].append(str(out / "cover.png"))
  830 [try_block ]     except Exception as e:
  831 [code      ]         fallback_notes.append(f"cover_png_fail: {e}")
  832 [try_block ]     try:
  833 [branch    ]         if _make_cover(out / "cover.jpg", title, artist, genre, size=1400, jpg=True):
  834 [code      ]             files.append(str(out / "cover.jpg"))
  835 [code      ]             cats["visuals"].append(str(out / "cover.jpg"))
  836 [try_block ]     except Exception as e:
  837 [code      ]         fallback_notes.append(f"cover_jpg_fail: {e}")
  838 [blank     ] 
  839 [comment   ]     # ---------- 9. ID3 tags on MP3 ----------
  840 [try_block ]     try:
  841 [code      ]         mp3_path = out / "full_master.mp3"
  842 [branch    ]         if mp3_path.exists():
  843 [code      ]             _apply_id3(mp3_path, meta, cover_path=out / "cover.jpg")
  844 [try_block ]     except Exception as e:
  845 [code      ]         fallback_notes.append(f"id3_fail: {e}")
  846 [blank     ] 
  847 [return    ]     return {
  848 [code      ]         "ok": len(files) > 0,
  849 [code      ]         "n_files": len(files),
  850 [code      ]         "files": files,
  851 [code      ]         "path": str(out),
  852 [code      ]         "categories": {k: len(v) for k, v in cats.items()},
  853 [code      ]         "fallback_used": bool(fallback_notes),
  854 [code      ]         "fallback_notes": fallback_notes,
  855 [code      ]     }
  856 [blank     ] 
  857 [blank     ] 
  858 [def       ] def _apply_id3(mp3_path: Path, meta: dict[str, Any], cover_path: Path):
  859 [import    ]     from mutagen.id3 import (
  860 [code      ]         APIC,
  861 [code      ]         ID3,
  862 [code      ]         TALB,
  863 [code      ]         TBPM,
  864 [code      ]         TCON,
  865 [code      ]         TDRC,
  866 [code      ]         TIT2,
  867 [code      ]         TKEY,
  868 [code      ]         TPE1,
  869 [code      ]         TPUB,
  870 [code      ]         TSRC,
  871 [code      ]     )
  872 [blank     ] 
  873 [try_block ]     try:
  874 [code      ]         id3 = ID3(str(mp3_path))
  875 [try_block ]     except Exception:
  876 [code      ]         id3 = ID3()
  877 [code      ]     id3.add(TIT2(encoding=3, text=meta.get("title", "ZS Track")))
  878 [code      ]     id3.add(TPE1(encoding=3, text=meta.get("artist", "ZS Artist")))
  879 [code      ]     id3.add(TALB(encoding=3, text=meta.get("album", meta.get("title", "ZS Track"))))
  880 [code      ]     id3.add(TCON(encoding=3, text=meta.get("genre", "Electronic")))
  881 [code      ]     id3.add(TBPM(encoding=3, text=str(meta.get("bpm", 140))))
  882 [code      ]     id3.add(TKEY(encoding=3, text=meta.get("key", "Am")))
  883 [comment   ]     # v39.4 (ШАГ 003): тег TSRC — от get_isrc, не placeholder
  884 [import    ]     from app.core.isrc import get_isrc as _get_isrc
  885 [code      ]     id3.add(TSRC(encoding=3, text=_get_isrc(meta, fallback="")))
  886 [code      ]     id3.add(TPUB(encoding=3, text="ZS Music Maker"))
  887 [code      ]     id3.add(TDRC(encoding=3, text=time.strftime("%Y")))
  888 [try_block ]     try:
  889 [branch    ]         if cover_path.exists():
  890 [stmt      ]             with open(cover_path, "rb") as f:
  891 [code      ]                 id3.add(
  892 [code      ]                     APIC(
  893 [code      ]                         encoding=3,
  894 [code      ]                         mime="image/jpeg",
  895 [code      ]                         type=3,
  896 [code      ]                         desc="Cover",
  897 [code      ]                         data=f.read(),
  898 [code      ]                     )
  899 [code      ]                 )
  900 [try_block ]     except Exception as e:
  901 [comment   ]         # v35: раньше молчало (pass) — обложка/теги терялись бесшумно.
  902 [comment   ]         # Не критично для аудио, но пользователь должен знать.
  903 [try_block ]         try:
  904 [import    ]             import sys as _s
  905 [code      ]             _s.stderr.write(f"[release_pack_full] ID3/cover embed failed: {e}\n")
  906 [try_block ]         except Exception:
  907 [code      ]             pass
  908 [code      ]     id3.save(str(mp3_path))
  909 [blank     ] 
  910 [blank     ] 
  911 [branch    ] if __name__ == "__main__":
  912 [comment   ]     # smoke
  913 [import    ]     import tempfile
  914 [blank     ] 
  915 [branch    ]     if sf is None:
  916 [code      ]         print("soundfile not available")
  917 [raise     ]         raise SystemExit(1)
  918 [code      ]     tmp = Path(tempfile.mkdtemp())
  919 [comment   ]     # 5-sec synthetic
  920 [code      ]     sr = 44100
  921 [import    ]     import numpy as _np
  922 [blank     ] 
  923 [code      ]     t = _np.linspace(0, 5, sr * 5, endpoint=False)
  924 [code      ]     data = 0.3 * _np.sin(2 * _np.pi * 220 * t).astype(_np.float32)
  925 [code      ]     data = _np.stack([data, data], axis=1)
  926 [code      ]     src = tmp / "synth.wav"
  927 [code      ]     sf.write(src, data, sr, subtype="PCM_16")
  928 [code      ]     meta = {
  929 [code      ]         "title": "Smoke Test",
  930 [code      ]         "artist": "ZS",
  931 [code      ]         "genre": "phonk",
  932 [code      ]         "bpm": 140,
  933 [code      ]         "key": "Am",
  934 [code      ]         "duration_sec": 5,
  935 [code      ]         "hashtags_youtube": ["music", "smoke"],
  936 [code      ]         "hashtags_vk": ["музыка"],
  937 [code      ]     }
  938 [code      ]     result = build_pack(
  939 [code      ]         str(src),
  940 [code      ]         str(tmp / "release"),
  941 [code      ]         meta,
  942 [code      ]         lyrics_text="Тест\nВторая строка\nТретья\n",
  943 [code      ]         hit_metrics={"score": 72, "verdict": "solid"},
  944 [code      ]     )
  945 [code      ]     print(
  946 [code      ]         json.dumps(
  947 [code      ]             {k: v for k, v in result.items() if k != "files"},
  948 [code      ]             ensure_ascii=False,
  949 [code      ]             indent=2,
  950 [code      ]         )
  951 [code      ]     )
  952 [code      ]     print("Files:", len(result["files"]))
```
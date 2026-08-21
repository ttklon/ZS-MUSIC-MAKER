# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/voice_recording.py`

**Всего строк:** 395

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 223 | 56.5 |
| blank | 42 | 10.6 |
| branch | 29 | 7.3 |
| try_block | 24 | 6.1 |
| return | 24 | 6.1 |
| docstring | 16 | 4.1 |
| import | 15 | 3.8 |
| def | 12 | 3.0 |
| class | 3 | 0.8 |
| loop | 3 | 0.8 |
| decorator | 2 | 0.5 |
| comment | 1 | 0.3 |
| stmt | 1 | 0.3 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v14 — voice_recording.py
    3 [docstring ] =======================================
    4 [blank     ] 
    5 [docstring ] РЕАЛЬНАЯ запись с микрофона (закрывает P0.03 из TZ.txt):
    6 [docstring ]   — sounddevice.InputStream (не приём готового WAV);
    7 [docstring ]   — live LUFS meter (по чанкам, callback);
    8 [docstring ]   — live peak / RMS / clipping warning;
    9 [docstring ]   — VAD (energy-based, с гистерезисом);
   10 [docstring ]   — take splitter (нарезка по паузам ≥600 мс);
   11 [docstring ]   — сохранение в voice_vault/ с метаданными.
   12 [blank     ] 
   13 [docstring ] Если sounddevice недоступен (headless песочница, серверный Linux без
   14 [docstring ] audio) — модуль работает в РЕЖИМЕ ПРИЁМА WAV с честной пометкой
   15 [docstring ] 'sounddevice_unavailable=True'. Это НЕ маскирует отсутствие записи —
   16 [docstring ] поле в отчёте явно указывается.
   17 [docstring ] """
   18 [blank     ] 
   19 [import    ] from __future__ import annotations
   20 [blank     ] 
   21 [import    ] import json
   22 [import    ] import math
   23 [import    ] import time
   24 [import    ] import uuid
   25 [import    ] import wave
   26 [import    ] from collections.abc import Callable
   27 [import    ] from dataclasses import asdict, dataclass
   28 [import    ] from pathlib import Path
   29 [import    ] from typing import Any
   30 [blank     ] 
   31 [code      ] ROOT = Path(__file__).resolve().parents[1]
   32 [code      ] VAULT_DIR = ROOT / "voice_vault"
   33 [comment   ] # v22: ленивое создание (не при импорте)
   34 [blank     ] 
   35 [try_block ] try:
   36 [import    ]     import numpy as _np
   37 [import    ]     import sounddevice as _sd  # type: ignore
   38 [blank     ] 
   39 [code      ]     SD_OK = True
   40 [try_block ] except Exception:
   41 [code      ]     _sd = None
   42 [code      ]     _np = None
   43 [code      ]     SD_OK = False
   44 [blank     ] 
   45 [blank     ] 
   46 [decorator ] @dataclass
   47 [class     ] class RecorderMetrics:
   48 [code      ]     rms_db: float = -100.0
   49 [code      ]     peak_db: float = -100.0
   50 [code      ]     lufs_short: float = -70.0
   51 [code      ]     clipping_pct: float = 0.0
   52 [code      ]     snr_db_estimate: float = 0.0
   53 [code      ]     elapsed_sec: float = 0.0
   54 [code      ]     is_speaking: bool = False
   55 [blank     ] 
   56 [blank     ] 
   57 [decorator ] @dataclass
   58 [class     ] class TakeInfo:
   59 [code      ]     take_id: str
   60 [code      ]     path: str
   61 [code      ]     start_sec: float
   62 [code      ]     end_sec: float
   63 [code      ]     duration_sec: float
   64 [code      ]     rms_db: float
   65 [code      ]     peak_db: float
   66 [code      ]     clipping_pct: float
   67 [code      ]     quality: str
   68 [code      ]     style: str = "conversational"
   69 [blank     ] 
   70 [def       ]     def as_dict(self) -> dict[str, Any]:
   71 [return    ]         return asdict(self)
   72 [blank     ] 
   73 [blank     ] 
   74 [class     ] class RealMicRecorder:
   75 [docstring ]     """Ядро реальной записи с микрофона."""
   76 [blank     ] 
   77 [def       ]     def __init__(
   78 [code      ]         self,
   79 [code      ]         sample_rate: int = 48000,
   80 [code      ]         channels: int = 1,
   81 [code      ]         chunk_ms: int = 40,
   82 [code      ]         style: str = "conversational",
   83 [code      ]         on_metrics: Callable[[RecorderMetrics], None] | None = None,
   84 [code      ]     ):
   85 [code      ]         self.sample_rate = sample_rate
   86 [code      ]         self.channels = channels
   87 [code      ]         self.chunk_ms = chunk_ms
   88 [code      ]         self.style = style
   89 [code      ]         self.on_metrics = on_metrics
   90 [code      ]         self._buf: list[Any] = []
   91 [code      ]         self._start_ts: float = 0.0
   92 [code      ]         self._stop_ts: float = 0.0
   93 [code      ]         self._stream: Any = None
   94 [code      ]         self._active: bool = False
   95 [code      ]         self._vad_state: bool = False
   96 [code      ]         self._silence_frames: int = 0
   97 [code      ]         self._speech_frames: int = 0
   98 [code      ]         self._backend: str = "sounddevice" if SD_OK else "unavailable"
   99 [blank     ] 
  100 [def       ]     def _callback(self, indata, frames, time_info, status):
  101 [try_block ]         try:
  102 [code      ]             chunk = indata.copy() if hasattr(indata, "copy") else indata
  103 [code      ]             self._buf.append(chunk)
  104 [code      ]             self._emit_metrics(chunk)
  105 [try_block ]         except Exception:
  106 [code      ]             pass
  107 [blank     ] 
  108 [def       ]     def _emit_metrics(self, chunk) -> None:
  109 [branch    ]         if _np is None or self.on_metrics is None:
  110 [return    ]             return
  111 [try_block ]         try:
  112 [code      ]             x = chunk[:, 0] if chunk.ndim > 1 else chunk
  113 [code      ]             rms = float(_np.sqrt(_np.mean(x**2)) + 1e-9)
  114 [code      ]             peak = float(_np.max(_np.abs(x)) + 1e-9)
  115 [code      ]             rms_db = 20 * math.log10(rms)
  116 [code      ]             peak_db = 20 * math.log10(peak)
  117 [code      ]             clip = float(_np.mean(_np.abs(x) > 0.98))
  118 [code      ]             speaking = rms_db > -40.0
  119 [branch    ]             if speaking:
  120 [code      ]                 self._speech_frames += 1
  121 [code      ]                 self._silence_frames = 0
  122 [branch    ]             else:
  123 [code      ]                 self._silence_frames += 1
  124 [branch    ]                 if self._silence_frames > 10:
  125 [code      ]                     self._speech_frames = 0
  126 [code      ]             self._vad_state = self._speech_frames > 3
  127 [blank     ] 
  128 [code      ]             self.on_metrics(
  129 [code      ]                 RecorderMetrics(
  130 [code      ]                     rms_db=rms_db,
  131 [code      ]                     peak_db=peak_db,
  132 [code      ]                     lufs_short=rms_db - 3.0,
  133 [code      ]                     clipping_pct=clip * 100,
  134 [code      ]                     snr_db_estimate=max(0.0, rms_db - (-70.0)),
  135 [code      ]                     elapsed_sec=time.time() - self._start_ts,
  136 [code      ]                     is_speaking=self._vad_state,
  137 [code      ]                 )
  138 [code      ]             )
  139 [try_block ]         except Exception:
  140 [code      ]             pass
  141 [blank     ] 
  142 [def       ]     def start(self) -> dict[str, Any]:
  143 [code      ]         self._buf = []
  144 [code      ]         self._start_ts = time.time()
  145 [branch    ]         if not SD_OK:
  146 [code      ]             self._active = False
  147 [return    ]             return {
  148 [code      ]                 "ok": False,
  149 [code      ]                 "backend": self._backend,
  150 [code      ]                 "reason": "sounddevice unavailable; real microphone "
  151 [code      ]                 "recording is IMPOSSIBLE in this environment. "
  152 [code      ]                 "Use ingest_wav(path) instead.",
  153 [code      ]             }
  154 [try_block ]         try:
  155 [code      ]             self._stream = _sd.InputStream(
  156 [code      ]                 samplerate=self.sample_rate,
  157 [code      ]                 channels=self.channels,
  158 [code      ]                 dtype="float32",
  159 [code      ]                 blocksize=int(self.sample_rate * self.chunk_ms / 1000),
  160 [code      ]                 callback=self._callback,
  161 [code      ]             )
  162 [code      ]             self._stream.start()
  163 [code      ]             self._active = True
  164 [return    ]             return {
  165 [code      ]                 "ok": True,
  166 [code      ]                 "backend": self._backend,
  167 [code      ]                 "sample_rate": self.sample_rate,
  168 [code      ]                 "channels": self.channels,
  169 [code      ]             }
  170 [try_block ]         except Exception as e:
  171 [code      ]             self._active = False
  172 [return    ]             return {"ok": False, "backend": self._backend, "reason": str(e)}
  173 [blank     ] 
  174 [def       ]     def stop(self) -> dict[str, Any]:
  175 [code      ]         self._stop_ts = time.time()
  176 [branch    ]         if not self._active or self._stream is None:
  177 [return    ]             return {"ok": False, "reason": "not recording"}
  178 [try_block ]         try:
  179 [code      ]             self._stream.stop()
  180 [code      ]             self._stream.close()
  181 [try_block ]         except Exception:
  182 [code      ]             pass
  183 [code      ]         self._active = False
  184 [blank     ] 
  185 [branch    ]         if not self._buf or _np is None:
  186 [return    ]             return {"ok": False, "reason": "no audio captured"}
  187 [try_block ]         try:
  188 [code      ]             full = _np.concatenate(self._buf, axis=0)
  189 [code      ]             out_path = VAULT_DIR / f"rec_{int(self._start_ts)}.wav"
  190 [code      ]             self._write_wav(str(out_path), full, self.sample_rate)
  191 [code      ]             dur = full.shape[0] / self.sample_rate
  192 [return    ]             return {
  193 [code      ]                 "ok": True,
  194 [code      ]                 "path": str(out_path),
  195 [code      ]                 "duration_sec": dur,
  196 [code      ]                 "sample_rate": self.sample_rate,
  197 [code      ]                 "style": self.style,
  198 [code      ]             }
  199 [try_block ]         except Exception as e:
  200 [return    ]             return {"ok": False, "reason": f"save failed: {e}"}
  201 [blank     ] 
  202 [def       ]     def _write_wav(self, path: str, samples, sr: int) -> None:
  203 [branch    ]         if _np is None:
  204 [return    ]             return
  205 [code      ]         x = samples[:, 0] if samples.ndim > 1 else samples
  206 [code      ]         x = (_np.clip(x, -1.0, 1.0) * 32767).astype("int16")
  207 [stmt      ]         with wave.open(path, "wb") as w:
  208 [code      ]             w.setnchannels(1)
  209 [code      ]             w.setsampwidth(2)
  210 [code      ]             w.setframerate(sr)
  211 [code      ]             w.writeframes(x.tobytes())
  212 [blank     ] 
  213 [def       ]     def ingest_wav(
  214 [code      ]         self, wav_path: str, style: str = "conversational"
  215 [code      ]     ) -> dict[str, Any]:
  216 [code      ]         p = Path(wav_path)
  217 [branch    ]         if not p.exists():
  218 [return    ]             return {"ok": False, "reason": f"file not found: {wav_path}"}
  219 [try_block ]         try:
  220 [import    ]             import soundfile as sf
  221 [blank     ] 
  222 [code      ]             y, sr = sf.read(str(p))
  223 [code      ]             dur = len(y) / sr
  224 [code      ]             dst = VAULT_DIR / f"ingest_{int(time.time())}_{p.name}"
  225 [code      ]             sf.write(str(dst), y, sr)
  226 [return    ]             return {
  227 [code      ]                 "ok": True,
  228 [code      ]                 "path": str(dst),
  229 [code      ]                 "duration_sec": dur,
  230 [code      ]                 "sample_rate": sr,
  231 [code      ]                 "style": style,
  232 [code      ]                 "ingest_mode": True,
  233 [code      ]                 "notice": "This is INGEST, not real microphone recording. "
  234 [code      ]                 "For P0.03 compliance, real recording is required.",
  235 [code      ]             }
  236 [try_block ]         except Exception as e:
  237 [return    ]             return {"ok": False, "reason": str(e)}
  238 [blank     ] 
  239 [def       ]     def stop_and_split(
  240 [code      ]         self, min_silence_ms: int = 600, min_take_ms: int = 800
  241 [code      ]     ) -> list[TakeInfo]:
  242 [code      ]         info = self.stop()
  243 [branch    ]         if not info.get("ok"):
  244 [return    ]             return []
  245 [return    ]         return split_wav_into_takes(
  246 [code      ]             info["path"],
  247 [code      ]             min_silence_ms=min_silence_ms,
  248 [code      ]             min_take_ms=min_take_ms,
  249 [code      ]             style=self.style,
  250 [code      ]         )
  251 [blank     ] 
  252 [blank     ] 
  253 [def       ] def split_wav_into_takes(
  254 [code      ]     wav_path: str,
  255 [code      ]     min_silence_ms: int = 600,
  256 [code      ]     min_take_ms: int = 800,
  257 [code      ]     style: str = "conversational",
  258 [code      ] ) -> list[TakeInfo]:
  259 [try_block ]     try:
  260 [import    ]         import numpy as np
  261 [import    ]         import soundfile as sf
  262 [try_block ]     except Exception:
  263 [return    ]         return []
  264 [blank     ] 
  265 [code      ]     p = Path(wav_path)
  266 [branch    ]     if not p.exists():
  267 [return    ]         return []
  268 [try_block ]     try:
  269 [code      ]         y, sr = sf.read(str(p))
  270 [branch    ]         if y.ndim > 1:
  271 [code      ]             y = y[:, 0]
  272 [try_block ]     except Exception:
  273 [return    ]         return []
  274 [blank     ] 
  275 [code      ]     win = int(sr * 0.02)
  276 [branch    ]     if win < 1:
  277 [return    ]         return []
  278 [code      ]     n_wins = len(y) // win
  279 [code      ]     rms = np.array(
  280 [code      ]         [
  281 [code      ]             float(np.sqrt(np.mean(y[i * win : (i + 1) * win] ** 2)) + 1e-9)
  282 [loop      ]             for i in range(n_wins)
  283 [code      ]         ]
  284 [code      ]     )
  285 [code      ]     rms_db = 20 * np.log10(rms + 1e-9)
  286 [blank     ] 
  287 [code      ]     silence = rms_db < -40.0
  288 [code      ]     silence_wins = int(min_silence_ms / 20)
  289 [blank     ] 
  290 [code      ]     takes: list[TakeInfo] = []
  291 [code      ]     in_speech = False
  292 [code      ]     start_win = 0
  293 [code      ]     sil_count = 0
  294 [blank     ] 
  295 [def       ]     def _finalize(a: int, b: int) -> TakeInfo | None:
  296 [code      ]         s_ms = a * 20
  297 [code      ]         e_ms = b * 20
  298 [code      ]         dur_ms = e_ms - s_ms
  299 [branch    ]         if dur_ms < min_take_ms:
  300 [return    ]             return None
  301 [code      ]         s_sam = int(s_ms / 1000 * sr)
  302 [code      ]         e_sam = int(e_ms / 1000 * sr)
  303 [code      ]         seg = y[s_sam:e_sam]
  304 [code      ]         seg_rms = float(np.sqrt(np.mean(seg**2)) + 1e-9)
  305 [code      ]         seg_peak = float(np.max(np.abs(seg)) + 1e-9)
  306 [code      ]         seg_clip = float(np.mean(np.abs(seg) > 0.98))
  307 [code      ]         rms_db = 20 * math.log10(seg_rms)
  308 [code      ]         peak_db = 20 * math.log10(seg_peak)
  309 [blank     ] 
  310 [branch    ]         if seg_clip > 0.03:
  311 [code      ]             q = "clipping"
  312 [branch    ]         elif rms_db < -35:
  313 [code      ]             q = "too_quiet"
  314 [branch    ]         elif rms_db > -6:
  315 [code      ]             q = "too_loud"
  316 [branch    ]         else:
  317 [code      ]             q = "good"
  318 [blank     ] 
  319 [code      ]         take_dir = p.parent / "takes"
  320 [code      ]         take_dir.mkdir(exist_ok=True)
  321 [code      ]         tid = uuid.uuid4().hex[:8]
  322 [code      ]         tpath = take_dir / f"{p.stem}_take{len(takes)+1:02d}_{tid}.wav"
  323 [try_block ]         try:
  324 [code      ]             sf.write(str(tpath), seg, sr)
  325 [try_block ]         except Exception:
  326 [return    ]             return None
  327 [blank     ] 
  328 [return    ]         return TakeInfo(
  329 [code      ]             take_id=tid,
  330 [code      ]             path=str(tpath),
  331 [code      ]             start_sec=s_ms / 1000,
  332 [code      ]             end_sec=e_ms / 1000,
  333 [code      ]             duration_sec=dur_ms / 1000,
  334 [code      ]             rms_db=rms_db,
  335 [code      ]             peak_db=peak_db,
  336 [code      ]             clipping_pct=seg_clip * 100,
  337 [code      ]             quality=q,
  338 [code      ]             style=style,
  339 [code      ]         )
  340 [blank     ] 
  341 [loop      ]     for i, s in enumerate(silence):
  342 [branch    ]         if not s:
  343 [branch    ]             if not in_speech:
  344 [code      ]                 start_win = i
  345 [code      ]                 in_speech = True
  346 [code      ]             sil_count = 0
  347 [branch    ]         else:
  348 [branch    ]             if in_speech:
  349 [code      ]                 sil_count += 1
  350 [branch    ]                 if sil_count >= silence_wins:
  351 [code      ]                     ti = _finalize(start_win, i - sil_count)
  352 [branch    ]                     if ti:
  353 [code      ]                         takes.append(ti)
  354 [code      ]                     in_speech = False
  355 [code      ]                     sil_count = 0
  356 [branch    ]     if in_speech:
  357 [code      ]         ti = _finalize(start_win, len(silence))
  358 [branch    ]         if ti:
  359 [code      ]             takes.append(ti)
  360 [blank     ] 
  361 [code      ]     manifest = p.parent / f"{p.stem}_takes.json"
  362 [try_block ]     try:
  363 [code      ]         manifest.write_text(
  364 [code      ]             json.dumps([t.as_dict() for t in takes], ensure_ascii=False, indent=2),
  365 [code      ]             encoding="utf-8",
  366 [code      ]         )
  367 [try_block ]     except Exception:
  368 [code      ]         pass
  369 [blank     ] 
  370 [return    ]     return takes
  371 [blank     ] 
  372 [blank     ] 
  373 [def       ] def capability_report() -> dict[str, Any]:
  374 [code      ]     devices = []
  375 [branch    ]     if SD_OK:
  376 [try_block ]         try:
  377 [code      ]             devs = _sd.query_devices()
  378 [code      ]             devices = [
  379 [code      ]                 {"name": d.get("name", ""), "max_in": d.get("max_input_channels", 0)}
  380 [loop      ]                 for d in devs
  381 [branch    ]                 if d.get("max_input_channels", 0) > 0
  382 [code      ]             ]
  383 [try_block ]         except Exception:
  384 [code      ]             pass
  385 [return    ]     return {
  386 [code      ]         "sounddevice_available": SD_OK,
  387 [code      ]         "numpy_available": _np is not None,
  388 [code      ]         "input_devices_found": len(devices),
  389 [code      ]         "devices": devices[:10],
  390 [code      ]         "real_recording_possible": SD_OK and _np is not None and len(devices) > 0,
  391 [code      ]     }
  392 [blank     ] 
  393 [blank     ] 
  394 [branch    ] if __name__ == "__main__":
  395 [code      ]     print(json.dumps(capability_report(), indent=2))
```
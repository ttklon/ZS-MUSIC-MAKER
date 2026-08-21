# grep-таблицы `app/core/orchestrator.py`

## `import` — 47 совпадений
```
   19 | from __future__ import annotations
   21 | import json
   22 | import time
   23 | from collections.abc import Callable
   24 | from dataclasses import dataclass, field
   25 | from pathlib import Path
   26 | from typing import Any
   29 |     from modules.llm_clients_v15 import LLMRouter
  245 |         from modules import analyzer
  276 |         from modules import groove_extractor
  307 |         from modules import arrangement_engine as ae
  324 |         from modules import beat_constructor as bc
  342 |                         import shutil
  379 |         import numpy as np
  380 |         import soundfile as sf
  576 |             from scipy.signal import butter as _bt
  577 |             from scipy.signal import sosfilt as _sf_
  638 |         import numpy as np
  639 |         import soundfile as sf
  694 |         from app.core import musicgen_texture as mgt
  914 |         from modules import voice_synth
  938 |         import pyttsx3
  959 |         import numpy as _np
  960 |         import soundfile as _sf
 1035 |                     from scipy.signal import butter, sosfilt
 1108 |         from modules import rvc_manager
 1138 |         import numpy as np
 1139 |         import soundfile as sf
 1148 |                 from scipy.signal import resample_poly
 1165 |             from scipy.signal import butter, sosfilt
 1183 |             import shutil
 1202 |         from modules import vocal_fx
 1239 |         from modules import sidechain
 1264 |         from modules import mastering
 1299 |             from modules import anti_neuro_v10 as an
 1316 |             from modules import anti_ai_polish as aap
 1341 |         import shutil
 1364 |         import demucs  # noqa
 1374 |         from modules import stem_splitter
 1431 |         from modules import hit_scorer
 1482 |         from modules.release_pack_full import build_pack as build_full
 1497 |         from modules import release_pack_v13 as rp
 1513 |         import shutil
 1521 |             from pydub import AudioSegment
 1530 |             from PIL import Image, ImageDraw
 1592 |             from modules import presets as _presets
 2043 |         import gradio as gr
```

## `except` — 49 совпадений
```
   30 | except Exception:
   96 |     except Exception as e:
  266 |     except Exception as e:
  301 |     except Exception as e:
  311 |     except Exception as e:
  345 |                     except Exception:
  360 |     except Exception as e:
  365 |         except Exception:
  594 |         except Exception:
  602 |             except Exception:
  621 |     except Exception as e:
  677 |     except Exception as e:
  700 |     except Exception:
  892 |         except Exception:
  923 |             except Exception:
  932 |     except Exception:
  951 |     except Exception:
 1044 |                 except Exception:
 1077 |     except Exception as e:
 1124 |     except RuntimeError as e:
 1126 |     except Exception as e:
 1154 |             except Exception:
 1171 |         except Exception:
 1181 |     except Exception:
 1187 |         except Exception:
 1217 |     except Exception as e:
 1252 |     except Exception as e:
 1286 |     except Exception as e:
 1311 |         except Exception:
 1337 |                     except Exception:
 1339 |         except Exception:
 1354 |     except Exception as e:
 1365 |     except Exception:
 1414 |     except Exception as e:
 1466 |     except Exception as e:
 1494 |     except Exception:
 1504 |     except Exception:
 1527 |         except Exception:
 1538 |         except Exception:
 1561 |     except Exception as e:
 1599 |         except Exception:
 1612 |     except Exception:
 1619 |     except Exception:
 1624 |     except Exception:
 1644 |     except Exception:
 1937 |         except Exception:
 1950 |         except Exception:
 1958 |         except Exception:
 2044 |     except Exception:
```

## `try` — 48 совпадений
```
   28 | try:
   87 |     try:
  244 |     try:
  275 |     try:
  306 |     try:
  323 |     try:
  341 |                     try:
  361 |         try:
  378 |     try:
  575 |         try:
  595 |             try:
  637 |     try:
  693 |     try:
  870 |         try:
  913 |     try:
  917 |             try:
  937 |     try:
  958 |     try:
 1034 |                 try:
 1107 |     try:
 1137 |     try:
 1147 |             try:
 1164 |         try:
 1182 |         try:
 1201 |     try:
 1236 |     try:
 1263 |     try:
 1292 |     try:
 1295 |         try:
 1315 |         try:
 1321 |                     try:
 1363 |     try:
 1373 |     try:
 1430 |     try:
 1481 |     try:
 1496 |     try:
 1512 |     try:
 1520 |         try:
 1529 |         try:
 1591 |         try:
 1610 |     try:
 1615 |     try:
 1622 |     try:
 1642 |     try:
 1902 |         try:
 1939 |         try:
 1953 |         try:
 2042 |     try:
```

## `def` — 40 совпадений
```
   38 | def _mark_legacy_result(result: Any, stage_name: str) -> dict[str, Any]:
   70 |     def to_dict(self) -> dict[str, Any]:
   84 | def _timed(name: str, fn: Callable[[], Any]) -> PipelineStage:
  103 | def _is_simulation_result(result: dict[str, Any]) -> bool:
  128 | def _is_blocked_result(result: dict[str, Any]) -> bool:
  135 | def _normalize_path_map(data: Any, keys: list[str] | None = None) -> dict[str, str]:
  232 | def _default_style_for_genre(genre: str) -> dict[str, Any]:
  237 | def _stage_analyze(
  270 | def _stage_groove(refs: list[str], genre: str = "drift_phonk") -> dict[str, Any]:
  305 | def _stage_arrangement(analysis: Any) -> dict[str, Any]:
  315 | def _stage_beat(
  369 | def _synth_beat(
  440 |         def _kick(sr_, dur=0.16):
  454 |         def _snare(sr_, dur=0.18):
  462 |         def _hat(sr_, dur=0.045, open_=False):
  469 |         def _808(sr_, dur, freq):
  476 |         def _riser(sr_, dur, kind="white"):
  625 | def _texture_scaffold(prompt: str, out_dir: Path) -> dict[str, Any]:
  687 | def _stage_texture(prompt: str, out_dir: Path) -> dict[str, Any]:
  704 | def _text_to_struct(text: str, genre: str) -> dict[str, Any]:
  742 | def _struct_to_text(struct: dict[str, Any]) -> str:
  848 | def _fallback_lyrics(theme: str, genre: str) -> dict[str, Any]:
  867 | def _stage_lyrics(theme: str, genre: str) -> dict[str, Any]:
  905 | def _stage_voice_synth(lyrics_text: str, out_dir: Path) -> dict[str, Any]:
  936 | def _pyttsx3_speak(text: str, out_wav: str) -> dict[str, Any]:
  983 |         def _extract_vowel(word: str) -> str:
 1092 | def _stage_rvc(
 1130 | def _mix_beat_and_vocal(
 1191 | def _stage_vocal_fx(vocal_wav: str | None, out_dir: Path) -> dict[str, Any]:
 1228 | def _stage_mix_and_sidechain(
 1256 | def _stage_mastering(
 1290 | def _stage_polish(input_wav: str, out_dir: Path) -> dict[str, Any]:
 1358 | def _stage_stems(master_wav: str, out_dir: Path) -> dict[str, Any]:
 1424 | def _stage_hit_score(master_wav: str) -> dict[str, Any]:
 1470 | def _stage_release_pack(
 1509 | def _minimal_release_pack(
 1568 | def run_full_pipeline(
 1980 |     def _stage_is_blocked(s):
 2041 | def build_gradio_ui():
 2047 |     def _run(refs_str, theme, genre):
```

## `class` — 2 совпадений
```
   47 | class PipelineStage:
   59 | class PipelineResult:
```

## `return` — 100 совпадений
```
   43 |     return marked
   71 |         return {
  100 |     return stage
  112 |         return False
  114 |         return False
  116 |         return True
  124 |             return True
  125 |     return False
  131 |         return False
  132 |     return bool(result.get("blocked"))
  138 |         return out
  150 |     return out
  234 |     return dict(_GENRE_STYLE_DEFAULTS.get(g, _GENRE_STYLE_DEFAULTS["drift_phonk"]))
  256 |             return {
  265 |         return {"ok": True, "analysis": res}
  267 |         return {"ok": False, "reason": str(e), "fallback_used": True}
  289 |             return {
  300 |         return {"ok": True, "groove": g}
  302 |         return {"ok": False, "reason": str(e)}
  310 |         return {"ok": True, "plan": plan}
  312 |         return {"ok": False, "reason": str(e)}
  347 |                 return {
  359 |         return _synth_beat(beat_wav, duration=_dur, bpm=_bpm)
  364 |             return _synth_beat(beat_wav, duration=_dur, bpm=_bpm)
  366 |             return {"ok": False, "reason": str(e)}
  452 |             return out
  460 |             return (body * 0.35 + air * 0.75) * env * 0.75
  467 |             return hp * env * (0.5 if open_ else 0.32)
  474 |             return np.tanh(osc * 1.6) * env * 0.85
  482 |                 return n * env * 0.35
  485 |             return np.sin(2 * np.pi * np.cumsum(f) / sr_).astype("float32") * env * 0.5
  611 |         return {
  622 |         return {"ok": False, "reason": str(e)}
  666 |         return {
  678 |         return {
  698 |             return r
  699 |         return _texture_scaffold(prompt, out_dir)
  701 |         return _texture_scaffold(prompt, out_dir)
  733 |     return {
  755 |     return "\n".join(parts)
  864 |     return out
  879 |                 return {
  895 |     return {
  908 |         return {
  922 |                     return {"ok": True, "path": path, "engine": "voice_synth.synth"}
  928 |                 return r
  930 |                 return {"ok": True, "path": r, "engine": "voice_synth"}
  931 |         return _pyttsx3_speak(lyrics_text, out_wav)
  933 |         return _pyttsx3_speak(lyrics_text, out_wav)
  944 |             return {
  987 |                     return v
  988 |             return "a"
 1065 |             return {
 1078 |         return {
 1084 |     return {
 1100 |         return {
 1113 |             return {
 1123 |         return {"ok": bool(r), "path": r or out_wav}
 1125 |         return {"ok": True, "blocked": True, "path": "", "reason": str(e)}
 1127 |         return {"ok": False, "reason": str(e)}
 1144 |             return out_wav
 1180 |         return out_wav
 1186 |             return out_wav
 1188 |             return None
 1200 |         return {"ok": False, "reason": "no vocal_wav upstream", "fallback_used": True}
 1207 |             return r
 1209 |         return {
 1218 |         return {
 1244 |             return r
 1245 |         return {
 1253 |         return {"ok": False, "reason": str(e)}
 1285 |         return r
 1287 |         return {"ok": False, "reason": str(e)}
 1304 |                     return _mark_legacy_result(r, legacy_attempt)
 1307 |                 return _mark_legacy_result(
 1327 |                             return r
 1336 |                             return result
 1353 |         return result
 1355 |         return {"ok": False, "reason": str(e)}
 1366 |         return {
 1383 |             return {
 1396 |                 return {
 1406 |             return {
 1413 |         return {"ok": True, "path": str(r), "engine": "stem_splitter." + fn.__name__}
 1416 |         return {
 1440 |             return {
 1449 |             return {"ok": False, "reason": f"hit_scorer.{fn.__name__} bad return type"}
 1451 |             return {
 1457 |         return {
 1467 |         return {"ok": False, "reason": f"{type(e).__name__}: {e}"}
 1484 |         return build_full(
 1503 |                 return r
 1506 |     return _minimal_release_pack(master_wav, meta, out)
 1553 |         return {
 1562 |         return {"ok": False, "reason": str(e)}
 1981 |         return bool(s.get("blocked")) or _is_blocked_result(s.get("output") or {})
 2038 |     return result.to_dict()
 2045 |         return None
 2054 |         return json.dumps(r, ensure_ascii=False, indent=2, default=str)
 2064 |     return demo
```

## `if` — 135 совпадений
```
   91 |         if isinstance(out, dict):
  111 |     if not isinstance(result, dict):
  113 |     if result.get("blocked"):
  115 |     if result.get("dry_run") or result.get("synthetic") or result.get("placeholder"):
  123 |         if marker in txt:
  130 |     if not isinstance(result, dict):
  137 |     if not isinstance(data, dict):
  141 |         if allow and name not in allow:
  144 |         if isinstance(value, (str, Path)):
  148 |         if path:
  247 |         if not refs:
  261 |         if len(refs) == 1:
  278 |         if not refs:
  294 |         if hasattr(groove_extractor, "extract_groove"):
  327 |         if hasattr(bc, "construct_beat"):
  337 |             if isinstance(r, dict) and r.get("beat_path"):
  340 |                 if src.exists() and src.resolve() != dst.resolve():
  415 |         if target_bars < total_bars:
  478 |             if kind == "white":
  492 |             if section_name == "intro":
  504 |             if section_name == "chorus":
  515 |                     if _kp[step] and section_name != "intro":
  519 |                     if snare_pat[step] and section_name != "intro":
  523 |                     if _hp[step]:
  528 |                     if _kp[step] and section_name != "intro":
  535 |                 if section_name == "pre" and bar == n_bars - 1:
  553 |             if section_name == "pre":
  555 |                 if sec_len > cut:
  606 |         if peak > 0.98:
  697 |         if isinstance(r, dict) and r.get("ok") and r.get("path"):
  713 |         if low.startswith("[") and low.endswith("]"):
  714 |             if "hook" in low or "chorus" in low or "припев" in low:
  723 |         if not title and len(ln) <= 60 and ln[0] not in "[(":
  725 |         if current == "verse1":
  731 |     if not title:
  744 |     if struct.get("title"):
  746 |     if struct.get("verse1"):
  749 |     if struct.get("chorus"):
  752 |     if struct.get("verse2"):
  860 |     if theme and theme not in ("лето, тачки, движ", "ночь", "движ"):
  862 |         if topic and len(topic) <= 40:
  869 |     if LLMRouter is not None:
  877 |             if r.get("ok") and r.get("text", "").strip():
  888 |                         if not r.get("fallback_used")
  907 |     if not lyrics_text or not lyrics_text.strip():
  916 |         if hasattr(voice_synth, "synth"):
  921 |                 if path and Path(path).exists() and Path(path).stat().st_size > 1000:
  925 |         if hasattr(voice_synth, "synthesize"):
  927 |             if isinstance(r, dict):
  929 |             if isinstance(r, str) and Path(r).exists():
  943 |         if Path(out_wav).exists() and Path(out_wav).stat().st_size > 1000:
  965 |         if not lines:
  986 |                 if v in wl:
 1012 |             if e_idx <= s_idx:
 1039 |                     if fc_hi > fc_lo:
 1052 |             if peak_seg > 0:
 1060 |         if peak > 0.9:
 1064 |         if Path(out_wav).exists() and Path(out_wav).stat().st_size > 1000:
 1099 |     if upstream_synthetic:
 1112 |         if not model_path.exists():
 1142 |         if not vocal_wav or not Path(vocal_wav).exists():
 1146 |         if sr_v != sr_b:
 1156 |         if voc.shape[1] == 1 and beat.shape[1] >= 2:
 1159 |         if voc.shape[0] < n:
 1176 |         if peak > 0.98:
 1199 |     if not vocal_wav or not Path(vocal_wav).exists():
 1206 |         if isinstance(r, dict) and r.get("ok") and r.get("path"):
 1243 |         if isinstance(r, dict) and r.get("out_wav"):
 1278 |         if stands:
 1280 |             if "streaming" not in _stands:
 1301 |             if hasattr(an, "polish_vocal"):
 1303 |                 if isinstance(r, dict) and r.get("ok"):
 1305 |             if hasattr(an, "apply_polish"):
 1320 |                 if callable(fn):
 1323 |                         if isinstance(r, dict) and r.get("ok"):
 1325 |                             if legacy_attempt:
 1328 |                         if isinstance(r, str) and Path(r).exists():
 1334 |                             if legacy_attempt:
 1351 |         if legacy_attempt:
 1379 |             if callable(f):
 1382 |         if fn is None:
 1391 |             if fn.__code__.co_argcount == 1
 1394 |         if isinstance(r, dict):
 1395 |             if "error" in r:
 1436 |             if callable(f):
 1439 |         if fn is None:
 1448 |         if not isinstance(r, dict):
 1450 |         if r.get("error"):
 1500 |         if hasattr(rp, "build_pack"):
 1502 |             if isinstance(r, dict):
 1590 |     if preset_key:
 1595 |             if isinstance(_p, dict) and "error" not in _p:
 1636 |     if voice_mode not in ("pro", "lazy", "off"):
 1639 |     if not isinstance(stands_req, list):
 1647 |     if quality_mode not in ("fast", "quality", "max"):
 1660 |     if user_extra_prompt and user_extra_prompt not in theme:
 1679 |     if isinstance(_preset_sv, dict):
 1680 |         if _preset_sv.get("target_bpm"):
 1682 |         if _preset_sv.get("target_mode"):
 1684 |         if _preset_sv.get("prompt_hint"):
 1686 |     if isinstance(analysis, dict):
 1687 |         if analysis.get("bpm"):
 1689 |         if analysis.get("mode"):
 1692 |     if bpm_override:
 1694 |         if isinstance(analysis, dict):
 1699 |     if duration_sec:
 1701 |     if user_aggression is not None:
 1722 |     if user_lyrics_lines:
 1724 |         if _own_text.strip():
 1742 |     if not user_lyrics_lines:
 1753 |     if voice_mode == "off":
 1788 |     if voice_mode != "off":
 1791 |             if isinstance(s7.output, dict)
 1794 |         if voice_wav:
 1812 |     if voice_mode != "off":
 1816 |         if s8.ok and _s8_path:
 1822 |         if vocal_final:
 1829 |         if s8b.ok and isinstance(s8b.output, dict):
 1837 |         if _voice_syn_synthetic and not (s8.ok and (s8.output or {}).get("path")):
 1844 |     if beat_wav:
 1854 |     if mix_wav:
 1866 |     if s10.ok and isinstance(s10.output, dict):
 1871 |     if streaming_master:
 1877 |     if streaming_master:
 1883 |     if streaming_master:
 1899 |     if streaming_master:
 1904 |             if isinstance(_mo, dict):
 1911 |                         if k
 1941 |             if isinstance(_so, dict):
 1945 |                     if k in ("drums", "bass", "vocals", "other")
 1954 |             if s13 and s13.output and isinstance(s13.output, dict):
 1989 |     if dry_run:
 1992 |         if any_sim:
 2017 |         if s.get("ok") and not _stage_is_blocked(s):
 2023 |     if any_sim and not dry_run:
```

## `for` — 19 совпадений
```
  118 |     for marker in (
  140 |     for name, value in data.items():
  489 |         for section_name, n_bars in sections:
  511 |             for bar in range(n_bars):
  513 |                 for step in range(16):
  539 |                     for h_i in range(n_hits):
  648 |         for det in (-6.0, 0.0, 5.0):
  711 |     for ln in lines:
  985 |             for v in vowel_list:
  996 |         for line_i, words in enumerate(words_per_line):
  997 |             for word in words:
 1009 |         for start_s, end_s, vowel, wlen in segments:
 1032 |             for f_c in (f1, f2, f3):
 1318 |             for cand in ("polish", "apply", "run", "process"):
 1377 |         for cand in ("split_stems", "split", "separate", "run"):
 1434 |         for cand in ("score_track", "score", "evaluate"):
 1910 |                         for k, v in _mo.items()
 1944 |                     for k, v in _so.items()
 2016 |     for s in stages:
```

## `with` — 1 совпадений
```
 2056 |     with gr.Blocks(title="ZS Music Maker (fallback UI)") as demo:
```

## `np` — 48 совпадений
```
  425 |         y = np.zeros(total_samples, dtype="float32")
  441 |             t = np.arange(int(sr_ * dur)) / sr_
  442 |             f = 90.0 * np.exp(-t * 18) + 45.0
  443 |             env = np.exp(-t * 11)
  444 |             body = np.sin(2 * np.pi * np.cumsum(f) / sr_) * env
  446 |                 np.random.randn(int(sr_ * 0.004)).astype("float32")
  447 |                 * np.exp(-np.arange(int(sr_ * 0.004)) / sr_ * 400)
  455 |             t = np.arange(int(sr_ * dur)) / sr_
  456 |             env = np.exp(-t * 17)
  457 |             noise = np.random.randn(len(t)).astype("float32")
  458 |             body = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 30)
  459 |             air = np.concatenate([[0], np.diff(noise)])
  463 |             t = np.arange(int(sr_ * dur)) / sr_
  464 |             env = np.exp(-t * (30 if open_ else 90))
  465 |             noise = np.random.randn(len(t)).astype("float32")
  466 |             hp = np.concatenate([[0], np.diff(noise)])
  470 |             t = np.arange(int(sr_ * dur)) / sr_
  471 |             env = np.exp(-t * 2.2) * (1.0 - np.exp(-t * 80.0))
  472 |             f = freq * (1.0 + 0.03 * np.exp(-t * 20))
  473 |             osc = np.sin(2 * np.pi * np.cumsum(f) / sr_)
  474 |             return np.tanh(osc * 1.6) * env * 0.85
  477 |             t = np.arange(int(sr_ * dur)) / sr_
  480 |                 n = np.random.randn(len(t)).astype("float32")
  481 |                 n = np.concatenate([[0], np.diff(n)])
  485 |             return np.sin(2 * np.pi * np.cumsum(f) / sr_).astype("float32") * env * 0.5
  583 |             mid_hi_r = np.concatenate(
  584 |                 [np.zeros(delay_samples, dtype="float32"), mid_hi[:-delay_samples]]
  590 |             hi_r = np.concatenate([np.zeros(d2, dtype="float32"), hi[:-d2]])
  593 |             stereo = np.stack([left, right], axis=1)
  598 |                 right = np.concatenate(
  599 |                     [np.zeros(delay_samples, dtype="float32"), y[:-delay_samples]]
  601 |                 stereo = np.stack([left, right], axis=1)
  603 |                 stereo = np.stack([y, y], axis=1)
  605 |         peak = float(np.max(np.abs(stereo)) + 1e-9)
  644 |         t = np.arange(n) / sr
  647 |         pad = np.zeros(n, dtype="float32")
  650 |             pad += np.sign(np.sin(2 * np.pi * f * t)) * 0.18
  652 |         env = np.sin(np.pi * t / dur) ** 2
  654 |         noise = np.random.randn(n).astype("float32")
  657 |         noise = np.convolve(noise, np.ones(k) / k, mode="same") * 0.06
  660 |         stereo = np.stack([y, np.roll(y, int(sr * 0.012))], axis=1)
  661 |         peak = float(np.max(np.abs(stereo))) + 1e-9
 1150 |                 voc = np.stack(
 1157 |             voc = np.repeat(voc, 2, axis=1)
 1160 |             pad = np.zeros((n - voc.shape[0], voc.shape[1]), dtype=voc.dtype)
 1161 |             voc = np.concatenate([voc, pad], axis=0)
 1168 |             voc = np.stack(
 1175 |         peak = float(np.max(np.abs(bus)) + 1e-9)
```

## `sf` — 6 совпадений
```
  610 |         sf.write(out_wav, stereo, sr)
  665 |         sf.write(out_wav, stereo, sr)
 1141 |         beat, sr_b = sf.read(beat_wav, always_2d=True)
 1143 |             sf.write(out_wav, beat, sr_b)
 1145 |         voc, sr_v = sf.read(vocal_wav, always_2d=True)
 1179 |         sf.write(out_wav, bus, sr_b)
```

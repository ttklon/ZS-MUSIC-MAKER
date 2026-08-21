# grep-таблицы `modules/beat_constructor.py`

## `import` — 10 совпадений
```
   19 | import json
   20 | import math
   21 | import os
   22 | import random
   24 | import numpy as np
  101 |             from pydub import AudioSegment
  547 |             from scipy.signal import butter as _bt26
  548 |             from scipy.signal import sosfilt as _sf26
  590 |             import soundfile as sf
  595 |                 from scipy.io import wavfile
```

## `print` — 3 совпадений
```
  111 |             print(f"[beat_constructor] load fail {path}: {e}")
  585 |             print(f"[beat_constructor] stereo width fallback: {exc}")
  658 |     print(json.dumps(result, ensure_ascii=False, indent=2))
```

## `except` — 6 совпадений
```
  110 |         except Exception as e:
  468 |         except Exception:
  526 |         except Exception:
  584 |         except Exception as exc:
  593 |         except Exception:
  599 |             except Exception:
```

## `try` — 6 совпадений
```
  100 |         try:
  454 |         try:
  472 |         try:
  546 |         try:
  589 |         try:
  594 |             try:
```

## `def` — 13 совпадений
```
   38 |     def __init__(
   60 |     def _classify_samples(self):
   98 |     def _load_audio(self, path: str) -> np.ndarray:
  114 |     def _generate_kick(self, step: int, bar: int) -> np.ndarray:
  151 |     def _generate_snare(self, step: int, bar: int) -> np.ndarray:
  180 |     def _generate_hihat(self, step: int, bar: int) -> np.ndarray:
  208 |     def _generate_bass_line(self, bar: int, bar_samples: int) -> np.ndarray:
  255 |     def _generate_melody(self, bar: int, section: str, bar_samples: int) -> np.ndarray:
  274 |     def _generate_fx(self, bar: int, section: str, bar_samples: int) -> np.ndarray:
  292 |     def _pan_audio(self, audio: np.ndarray, pan: float) -> np.ndarray:
  302 |     def _build_section(
  394 |     def build_track(
  621 | def construct_beat(
```

## `class` — 1 совпадений
```
   35 | class BeatConstructor:
```

## `return` — 24 совпадений
```
  109 |             return samples
  112 |             return np.zeros(self.sr, dtype=np.float32)
  129 |             return np.zeros(1, dtype=np.float32)
  141 |             return self._load_audio(kick_path) * velocity
  149 |         return kick
  163 |                 return np.zeros(1, dtype=np.float32)
  169 |             return self._load_audio(snare_path) * velocity
  178 |         return snare
  191 |             return np.zeros(1, dtype=np.float32)
  195 |             return self._load_audio(hh_path) * 0.5  # хэт тише
  206 |         return hihat
  215 |             return bass[:bar_samples] * 0.8
  253 |         return bass
  263 |             return mel[:bar_samples] * 0.4
  270 |             return mel[:bar_samples]
  272 |         return np.zeros(bar_samples, dtype=np.float32)
  282 |             return fx[:bar_samples] * 0.5
  288 |             return np.pad(fx, (bar_samples - stop_samples, 0))
  290 |         return np.zeros(bar_samples, dtype=np.float32)
  295 |             return audio  # уже стерео
  300 |         return np.stack([audio * left, audio * right], axis=1).astype(np.float32)
  392 |         return section_audio
  602 |         return {
  640 |     return bc.build_track(
```

## `if` — 42 совпадений
```
   64 |             if any(k in name for k in ["kick", "bd", "bass_drum", "808"]):
  104 |             if seg.channels > 1:
  122 |         if bar % 4 == 3 and step >= 12:
  124 |             if step in [12, 14, 15]:
  128 |         if kick_pattern[idx] == 0:
  133 |         if step == 0:
  139 |         if self.kick_samples:
  159 |         if snare_pattern[step % 16] == 0:
  160 |             if step % 16 in [3, 6, 11, 14] and random.random() < 0.2:
  167 |         if self.snare_samples:
  187 |         if step % 2 == 1 and random.random() < swing * 0.5:
  190 |         if not play:
  193 |         if self.hihat_samples:
  203 |         if len(noise) > 10:
  210 |         if self.bass_samples:
  213 |             if len(bass) < bar_samples:
  244 |             if play:
  258 |         if section in ("intro", "breakdown", "outro") and self.melody_samples:
  261 |             if len(mel) < bar_samples:
  265 |         if section == "verse" and self.melody_samples and bar % 2 == 0:
  268 |             if len(mel) < bar_samples:
  277 |         if section == "pre_chorus" and self.fx_samples:
  280 |             if len(fx) < bar_samples:
  285 |         if section == "hook" and bar % 4 == 3:
  294 |         if audio.ndim > 1:
  318 |             if section not in ("intro_pad", "breakdown_silent", "outro_fade"):
  323 |             if section not in ("intro_pad", "breakdown_silent"):
  358 |             if bar >= n_bars // 2 and section in ("verse", "hook"):
  370 |             if peak > 1.0:
  421 |         if include_intro:
  430 |         if include_outro:
  457 |                 if _info["name"] in ("hook", "chorus"):
  460 |             if _first_hook_sec is not None:
  463 |                 if _idx - _fade > 0:
  492 |                 if _mode.startswith("maj")
  503 |                 if _info["name"] not in ("hook", "chorus"):
  531 |         if len(full_track) > target_samples:
  538 |         if peak > 0:
  550 |             if stereo.ndim == 2 and stereo.shape[1] >= 2:
  571 |                 if _seed_rms > 1e-8 and _mid_rms > 1e-8:
  582 |             if _pk > 0.98:
  648 | if __name__ == "__main__":
```

## `for` — 12 совпадений
```
   62 |         for s in self.samples:
   76 |                 for k in [
   91 |                 for k in ["fx", "rise", "riser", "sweep", "impact", "sfx", "noise"]
  243 |         for i, play in enumerate(kick_pattern):
  313 |         for bar in range(n_bars):
  324 |                 for step in range(16):
  360 |                 for off_step in [7, 15]:
  426 |         for v in range(1, n_verses):
  438 |         for section_name, n_bars in sections:
  456 |             for _info in section_info:
  502 |             for _info in section_info:
  634 |     for ind in style_vector.get("individual", []):
```

## `while` — 1 совпадений
```
  512 |                 while _pos + _ns < _hs + _hn and _pos + _ns < len(full_track):
```

## `np` — 63 совпадений
```
   98 |     def _load_audio(self, path: str) -> np.ndarray:
  107 |             samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
  112 |             return np.zeros(self.sr, dtype=np.float32)
  114 |     def _generate_kick(self, step: int, bar: int) -> np.ndarray:
  129 |             return np.zeros(1, dtype=np.float32)
  145 |         t = np.linspace(0, dur, int(self.sr * dur), endpoint=False)
  146 |         env = np.exp(-t * 30)
  147 |         freq = 60 * np.exp(-t * 100) + 40  # pitch sweep
  148 |         kick = 0.8 * env * np.sin(2 * np.pi * freq * t)
  151 |     def _generate_snare(self, step: int, bar: int) -> np.ndarray:
  163 |                 return np.zeros(1, dtype=np.float32)
  173 |         t = np.linspace(0, dur, int(self.sr * dur), endpoint=False)
  174 |         env = np.exp(-t * 25)
  175 |         noise = np.random.randn(len(t)) * 0.5
  176 |         tone = 0.3 * np.sin(2 * np.pi * 200 * t)
  180 |     def _generate_hihat(self, step: int, bar: int) -> np.ndarray:
  191 |             return np.zeros(1, dtype=np.float32)
  199 |         t = np.linspace(0, dur, int(self.sr * dur), endpoint=False)
  200 |         env = np.exp(-t * 80)
  201 |         noise = np.random.randn(len(t))
  204 |             noise = noise - np.convolve(noise, np.ones(10) / 10, mode="same")
  208 |     def _generate_bass_line(self, bar: int, bar_samples: int) -> np.ndarray:
  214 |                 bass = np.pad(bass, (0, bar_samples - len(bass)))
  240 |         bass = np.zeros(bar_samples, dtype=np.float32)
  247 |                 dur_t = np.linspace(
  250 |                 env = np.exp(-dur_t * 5)
  251 |                 bass[start:end] += 0.7 * env * np.sin(2 * np.pi * base_freq * dur_t)
  255 |     def _generate_melody(self, bar: int, section: str, bar_samples: int) -> np.ndarray:
  262 |                 mel = np.pad(mel, (0, bar_samples - len(mel)))
  269 |                 mel = np.pad(mel, (0, bar_samples - len(mel)))
  272 |         return np.zeros(bar_samples, dtype=np.float32)
  274 |     def _generate_fx(self, bar: int, section: str, bar_samples: int) -> np.ndarray:
  281 |                 fx = np.pad(fx, (0, bar_samples - len(fx)))
  287 |             fx = np.ones(stop_samples, dtype=np.float32) * 0.001
  288 |             return np.pad(fx, (bar_samples - stop_samples, 0))
  290 |         return np.zeros(bar_samples, dtype=np.float32)
  292 |     def _pan_audio(self, audio: np.ndarray, pan: float) -> np.ndarray:
  300 |         return np.stack([audio * left, audio * right], axis=1).astype(np.float32)
  304 |     ) -> np.ndarray:
  311 |         section_audio = np.zeros((bar_samples * n_bars, 2), dtype=np.float32)
  315 |             bar_audio = np.zeros((bar_samples, 2), dtype=np.float32)
  369 |             peak = np.max(np.abs(bar_audio)) + 1e-9
  451 |         full_track = np.concatenate(all_audio, axis=0)
  464 |                     _env = np.linspace(1.0, 0.02, _fade).astype(np.float32)[
  465 |                         :, np.newaxis
  508 |                 _t = np.arange(_ns, dtype=np.float32) / self.sr
  509 |                 _env = np.exp(-_t * 4.0) * (1.0 - np.exp(-_t * 60.0))
  515 |                         0.6 * np.sin(2 * np.pi * _f * _t)
  516 |                         + 0.25 * np.sin(2 * np.pi * _f * 2 * _t)
  517 |                         + 0.10 * np.sin(2 * np.pi * _f * 3 * _t)
  522 |                         self._pan_audio(_lead.astype(np.float32), _lead_pan) * 0.12
  534 |             full_track = np.pad(
  537 |         peak = np.max(np.abs(full_track)) + 1e-9
  545 |         stereo = np.asarray(full_track, dtype=np.float32).copy()
  560 |                 _delayed = np.zeros_like(_high_mid)
  563 |                 _seed_rms = float(np.sqrt(np.mean(_width_seed ** 2)) + 1e-12)
  564 |                 _mid_rms = float(np.sqrt(np.mean(_mid ** 2)) + 1e-12)
  565 |                 _side_rms = float(np.sqrt(np.mean(_side ** 2)) + 1e-12)
  574 |                         np.sqrt(np.mean(_candidate_side ** 2)) + 1e-12
  577 |                     stereo = np.column_stack((_mid + _side, _mid - _side)).astype(
  578 |                         np.float32, copy=False
  581 |             _pk = float(np.max(np.abs(stereo)) + 1e-9)
  598 |                 wavfile.write(out_path, self.sr, (stereo * 32767).astype(np.int16))
```

## `sf` — 1 совпадений
```
  592 |             sf.write(out_path, stereo, self.sr, subtype="PCM_16")
```

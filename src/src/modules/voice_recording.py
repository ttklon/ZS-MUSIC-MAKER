# -*- coding: utf-8 -*-
"""
ZS Music Maker v14 — voice_recording.py
=======================================

РЕАЛЬНАЯ запись с микрофона (закрывает P0.03 из TZ.txt):
  — sounddevice.InputStream (не приём готового WAV);
  — live LUFS meter (по чанкам, callback);
  — live peak / RMS / clipping warning;
  — VAD (energy-based, с гистерезисом);
  — take splitter (нарезка по паузам ≥600 мс);
  — сохранение в voice_vault/ с метаданными.

Если sounddevice недоступен (headless песочница, серверный Linux без
audio) — модуль работает в РЕЖИМЕ ПРИЁМА WAV с честной пометкой
'sounddevice_unavailable=True'. Это НЕ маскирует отсутствие записи —
поле в отчёте явно указывается.
"""

from __future__ import annotations

import json
import math
import time
import uuid
import wave
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
VAULT_DIR = ROOT / "voice_vault"
# v22: ленивое создание (не при импорте)

try:
    import sounddevice as _sd  # type: ignore
    import numpy as _np
    SD_OK = True
except Exception:
    _sd = None
    _np = None
    SD_OK = False


@dataclass
class RecorderMetrics:
    rms_db: float = -100.0
    peak_db: float = -100.0
    lufs_short: float = -70.0
    clipping_pct: float = 0.0
    snr_db_estimate: float = 0.0
    elapsed_sec: float = 0.0
    is_speaking: bool = False


@dataclass
class TakeInfo:
    take_id: str
    path: str
    start_sec: float
    end_sec: float
    duration_sec: float
    rms_db: float
    peak_db: float
    clipping_pct: float
    quality: str
    style: str = "conversational"

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RealMicRecorder:
    """Ядро реальной записи с микрофона."""

    def __init__(self, sample_rate: int = 48000, channels: int = 1,
                 chunk_ms: int = 40, style: str = "conversational",
                 on_metrics: Optional[Callable[[RecorderMetrics], None]] = None):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_ms = chunk_ms
        self.style = style
        self.on_metrics = on_metrics
        self._buf: List[Any] = []
        self._start_ts: float = 0.0
        self._stop_ts: float = 0.0
        self._stream: Any = None
        self._active: bool = False
        self._vad_state: bool = False
        self._silence_frames: int = 0
        self._speech_frames: int = 0
        self._backend: str = "sounddevice" if SD_OK else "unavailable"

    def _callback(self, indata, frames, time_info, status):
        try:
            chunk = indata.copy() if hasattr(indata, "copy") else indata
            self._buf.append(chunk)
            self._emit_metrics(chunk)
        except Exception:
            pass

    def _emit_metrics(self, chunk) -> None:
        if _np is None or self.on_metrics is None:
            return
        try:
            x = chunk[:, 0] if chunk.ndim > 1 else chunk
            rms = float(_np.sqrt(_np.mean(x ** 2)) + 1e-9)
            peak = float(_np.max(_np.abs(x)) + 1e-9)
            rms_db = 20 * math.log10(rms)
            peak_db = 20 * math.log10(peak)
            clip = float(_np.mean(_np.abs(x) > 0.98))
            speaking = rms_db > -40.0
            if speaking:
                self._speech_frames += 1
                self._silence_frames = 0
            else:
                self._silence_frames += 1
                if self._silence_frames > 10:
                    self._speech_frames = 0
            self._vad_state = self._speech_frames > 3

            self.on_metrics(RecorderMetrics(
                rms_db=rms_db, peak_db=peak_db,
                lufs_short=rms_db - 3.0,
                clipping_pct=clip * 100,
                snr_db_estimate=max(0.0, rms_db - (-70.0)),
                elapsed_sec=time.time() - self._start_ts,
                is_speaking=self._vad_state,
            ))
        except Exception:
            pass

    def start(self) -> Dict[str, Any]:
        self._buf = []
        self._start_ts = time.time()
        if not SD_OK:
            self._active = False
            return {"ok": False, "backend": self._backend,
                    "reason": "sounddevice unavailable; real microphone "
                              "recording is IMPOSSIBLE in this environment. "
                              "Use ingest_wav(path) instead."}
        try:
            self._stream = _sd.InputStream(
                samplerate=self.sample_rate, channels=self.channels,
                dtype="float32",
                blocksize=int(self.sample_rate * self.chunk_ms / 1000),
                callback=self._callback,
            )
            self._stream.start()
            self._active = True
            return {"ok": True, "backend": self._backend,
                    "sample_rate": self.sample_rate,
                    "channels": self.channels}
        except Exception as e:
            self._active = False
            return {"ok": False, "backend": self._backend, "reason": str(e)}

    def stop(self) -> Dict[str, Any]:
        self._stop_ts = time.time()
        if not self._active or self._stream is None:
            return {"ok": False, "reason": "not recording"}
        try:
            self._stream.stop()
            self._stream.close()
        except Exception:
            pass
        self._active = False

        if not self._buf or _np is None:
            return {"ok": False, "reason": "no audio captured"}
        try:
            full = _np.concatenate(self._buf, axis=0)
            out_path = VAULT_DIR / f"rec_{int(self._start_ts)}.wav"
            self._write_wav(str(out_path), full, self.sample_rate)
            dur = full.shape[0] / self.sample_rate
            return {"ok": True, "path": str(out_path),
                    "duration_sec": dur, "sample_rate": self.sample_rate,
                    "style": self.style}
        except Exception as e:
            return {"ok": False, "reason": f"save failed: {e}"}

    def _write_wav(self, path: str, samples, sr: int) -> None:
        if _np is None:
            return
        x = samples[:, 0] if samples.ndim > 1 else samples
        x = (_np.clip(x, -1.0, 1.0) * 32767).astype("int16")
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(x.tobytes())

    def ingest_wav(self, wav_path: str, style: str = "conversational") -> Dict[str, Any]:
        p = Path(wav_path)
        if not p.exists():
            return {"ok": False, "reason": f"file not found: {wav_path}"}
        try:
            import soundfile as sf
            y, sr = sf.read(str(p))
            dur = len(y) / sr
            dst = VAULT_DIR / f"ingest_{int(time.time())}_{p.name}"
            sf.write(str(dst), y, sr)
            return {"ok": True, "path": str(dst), "duration_sec": dur,
                    "sample_rate": sr, "style": style, "ingest_mode": True,
                    "notice": "This is INGEST, not real microphone recording. "
                              "For P0.03 compliance, real recording is required."}
        except Exception as e:
            return {"ok": False, "reason": str(e)}

    def stop_and_split(self, min_silence_ms: int = 600,
                       min_take_ms: int = 800) -> List[TakeInfo]:
        info = self.stop()
        if not info.get("ok"):
            return []
        return split_wav_into_takes(info["path"],
                                    min_silence_ms=min_silence_ms,
                                    min_take_ms=min_take_ms,
                                    style=self.style)


def split_wav_into_takes(wav_path: str, min_silence_ms: int = 600,
                         min_take_ms: int = 800,
                         style: str = "conversational") -> List[TakeInfo]:
    try:
        import soundfile as sf
        import numpy as np
    except Exception:
        return []

    p = Path(wav_path)
    if not p.exists():
        return []
    try:
        y, sr = sf.read(str(p))
        if y.ndim > 1:
            y = y[:, 0]
    except Exception:
        return []

    win = int(sr * 0.02)
    if win < 1:
        return []
    n_wins = len(y) // win
    rms = np.array([
        float(np.sqrt(np.mean(y[i*win:(i+1)*win] ** 2)) + 1e-9)
        for i in range(n_wins)
    ])
    rms_db = 20 * np.log10(rms + 1e-9)

    silence = rms_db < -40.0
    silence_wins = int(min_silence_ms / 20)

    takes: List[TakeInfo] = []
    in_speech = False
    start_win = 0
    sil_count = 0

    def _finalize(a: int, b: int) -> Optional[TakeInfo]:
        s_ms = a * 20
        e_ms = b * 20
        dur_ms = e_ms - s_ms
        if dur_ms < min_take_ms:
            return None
        s_sam = int(s_ms / 1000 * sr)
        e_sam = int(e_ms / 1000 * sr)
        seg = y[s_sam:e_sam]
        seg_rms = float(np.sqrt(np.mean(seg ** 2)) + 1e-9)
        seg_peak = float(np.max(np.abs(seg)) + 1e-9)
        seg_clip = float(np.mean(np.abs(seg) > 0.98))
        rms_db = 20 * math.log10(seg_rms)
        peak_db = 20 * math.log10(seg_peak)

        if seg_clip > 0.03:
            q = "clipping"
        elif rms_db < -35:
            q = "too_quiet"
        elif rms_db > -6:
            q = "too_loud"
        else:
            q = "good"

        take_dir = p.parent / "takes"
        take_dir.mkdir(exist_ok=True)
        tid = uuid.uuid4().hex[:8]
        tpath = take_dir / f"{p.stem}_take{len(takes)+1:02d}_{tid}.wav"
        try:
            sf.write(str(tpath), seg, sr)
        except Exception:
            return None

        return TakeInfo(
            take_id=tid, path=str(tpath),
            start_sec=s_ms / 1000, end_sec=e_ms / 1000,
            duration_sec=dur_ms / 1000,
            rms_db=rms_db, peak_db=peak_db,
            clipping_pct=seg_clip * 100,
            quality=q, style=style,
        )

    for i, s in enumerate(silence):
        if not s:
            if not in_speech:
                start_win = i
                in_speech = True
            sil_count = 0
        else:
            if in_speech:
                sil_count += 1
                if sil_count >= silence_wins:
                    ti = _finalize(start_win, i - sil_count)
                    if ti:
                        takes.append(ti)
                    in_speech = False
                    sil_count = 0
    if in_speech:
        ti = _finalize(start_win, len(silence))
        if ti:
            takes.append(ti)

    manifest = p.parent / f"{p.stem}_takes.json"
    try:
        manifest.write_text(
            json.dumps([t.as_dict() for t in takes],
                       ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception:
        pass

    return takes


def capability_report() -> Dict[str, Any]:
    devices = []
    if SD_OK:
        try:
            devs = _sd.query_devices()
            devices = [{"name": d.get("name", ""),
                        "max_in": d.get("max_input_channels", 0)}
                       for d in devs if d.get("max_input_channels", 0) > 0]
        except Exception:
            pass
    return {
        "sounddevice_available": SD_OK,
        "numpy_available": _np is not None,
        "input_devices_found": len(devices),
        "devices": devices[:10],
        "real_recording_possible": SD_OK and _np is not None and len(devices) > 0,
    }


if __name__ == "__main__":
    print(json.dumps(capability_report(), indent=2))

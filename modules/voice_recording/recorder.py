# -*- coding: utf-8 -*-
"""
modules/voice_recording/recorder.py — живая запись с микрофона.

`sounddevice.InputStream` + колбэк на чанк: метрики уровня (RMS/peak/LUFS-подобный),
VAD с гистерезисом и накопление буфера. Ошибки реального времени не летят в
пользователя, а складываются в `last_error`.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from modules.voice_recording.state import (
    SD_OK,
    VAULT_DIR,
    RecorderMetrics,
    _np,
    _sd,
)


class RealMicRecorder:
    """Ядро реальной записи с микрофона."""

    def __init__(
        self,
        sample_rate: int = 48000,
        channels: int = 1,
        chunk_ms: int = 40,
        style: str = "conversational",
        on_metrics: Callable[[RecorderMetrics], None] | None = None,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_ms = chunk_ms
        self.style = style
        self.on_metrics = on_metrics
        self._buf: list[Any] = []
        self._start_ts: float = 0.0
        self._stop_ts: float = 0.0
        self._stream: Any = None
        self._active: bool = False
        self._vad_state: bool = False
        self._silence_frames: int = 0
        self._speech_frames: int = 0
        self._backend: str = "sounddevice" if SD_OK else "unavailable"
        self.last_error: str | None = None

    def _record_error(self, context: str, error: Exception) -> None:
        """Retain non-fatal real-time recorder failures for caller inspection."""
        self.last_error = f"{context}: {type(error).__name__}: {error}"

    def _callback(self, indata, frames, time_info, status):
        try:
            chunk = indata.copy() if hasattr(indata, "copy") else indata
            self._buf.append(chunk)
            self._emit_metrics(chunk)
        except Exception as error:
            self._record_error("audio callback", error)

    def _emit_metrics(self, chunk) -> None:
        if _np is None or self.on_metrics is None:
            return
        try:
            x = chunk[:, 0] if chunk.ndim > 1 else chunk
            rms = float(_np.sqrt(_np.mean(x**2)) + 1e-9)
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

            self.on_metrics(
                RecorderMetrics(
                    rms_db=rms_db,
                    peak_db=peak_db,
                    lufs_short=rms_db - 3.0,
                    clipping_pct=clip * 100,
                    snr_db_estimate=max(0.0, rms_db - (-70.0)),
                    elapsed_sec=time.time() - self._start_ts,
                    is_speaking=self._vad_state,
                )
            )
        except Exception as error:
            self._record_error("metrics callback", error)

    def start(self) -> dict[str, Any]:
        self._buf = []
        self._start_ts = time.time()
        if not SD_OK:
            self._active = False
            return {
                "ok": False,
                "backend": self._backend,
                "reason": "sounddevice unavailable; real microphone "
                "recording is IMPOSSIBLE in this environment. "
                "Use ingest_wav(path) instead.",
            }
        try:
            self._stream = _sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                blocksize=int(self.sample_rate * self.chunk_ms / 1000),
                callback=self._callback,
            )
            self._stream.start()
            self._active = True
            return {
                "ok": True,
                "backend": self._backend,
                "sample_rate": self.sample_rate,
                "channels": self.channels,
            }
        except Exception as e:
            self._active = False
            return {"ok": False, "backend": self._backend, "reason": str(e)}

    def stop(self) -> dict[str, Any]:
        self._stop_ts = time.time()
        if not self._active or self._stream is None:
            return {"ok": False, "reason": "not recording"}
        try:
            self._stream.stop()
            self._stream.close()
        except Exception as error:
            self._record_error("stream shutdown", error)
        self._active = False

        if not self._buf or _np is None:
            return {"ok": False, "reason": "no audio captured"}
        try:
            full = _np.concatenate(self._buf, axis=0)
            out_path = VAULT_DIR / f"rec_{int(self._start_ts)}.wav"
            self._write_wav(str(out_path), full, self.sample_rate)
            dur = full.shape[0] / self.sample_rate
            return {
                "ok": True,
                "path": str(out_path),
                "duration_sec": dur,
                "sample_rate": self.sample_rate,
                "style": self.style,
            }
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

    def ingest_wav(
        self, wav_path: str, style: str = "conversational"
    ) -> dict[str, Any]:
        p = Path(wav_path)
        if not p.exists():
            return {"ok": False, "reason": f"file not found: {wav_path}"}
        try:
            import soundfile as sf

            y, sr = sf.read(str(p))
            dur = len(y) / sr
            dst = VAULT_DIR / f"ingest_{int(time.time())}_{p.name}"
            sf.write(str(dst), y, sr)
            return {
                "ok": True,
                "path": str(dst),
                "duration_sec": dur,
                "sample_rate": sr,
                "style": style,
                "ingest_mode": True,
                "notice": "This is INGEST, not real microphone recording. "
                "For P0.03 compliance, real recording is required.",
            }
        except Exception as e:
            return {"ok": False, "reason": str(e)}

    def stop_and_split(
        self, min_silence_ms: int = 600, min_take_ms: int = 800
    ) -> list[TakeInfo]:
        info = self.stop()
        if not info.get("ok"):
            return []
        return split_wav_into_takes(
            info["path"],
            min_silence_ms=min_silence_ms,
            min_take_ms=min_take_ms,
            style=self.style,
        )

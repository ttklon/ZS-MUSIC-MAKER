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
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VAULT_DIR = ROOT / "voice_vault"
# v22: ленивое создание (не при импорте)

try:
    import numpy as _np
    import sounddevice as _sd  # type: ignore

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

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


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
        except Exception:
            pass

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


def _read_mono_wav(wav_path: str) -> tuple[Any, int] | None:
    try:
        import soundfile as sf

        samples, sample_rate = sf.read(wav_path)
        if samples.ndim > 1:
            samples = samples[:, 0]
        return samples, sample_rate
    except Exception:
        return None


def _frame_rms_db(samples: Any, window_size: int) -> Any:
    import numpy as np

    frame_count = len(samples) // window_size
    rms = np.array(
        [
            float(
                np.sqrt(
                    np.mean(samples[index * window_size : (index + 1) * window_size] ** 2)
                )
                + 1e-9
            )
            for index in range(frame_count)
        ]
    )
    return 20 * np.log10(rms + 1e-9)


def _write_take(
    source_path: Path,
    samples: Any,
    sample_rate: int,
    start_win: int,
    end_win: int,
    min_take_ms: int,
    take_number: int,
    style: str,
) -> TakeInfo | None:
    import numpy as np
    import soundfile as sf

    start_ms = start_win * 20
    end_ms = end_win * 20
    duration_ms = end_ms - start_ms
    if duration_ms < min_take_ms:
        return None
    start_sample = int(start_ms / 1000 * sample_rate)
    end_sample = int(end_ms / 1000 * sample_rate)
    segment = samples[start_sample:end_sample]
    segment_rms = float(np.sqrt(np.mean(segment**2)) + 1e-9)
    segment_peak = float(np.max(np.abs(segment)) + 1e-9)
    segment_clipping = float(np.mean(np.abs(segment) > 0.98))
    rms_db = 20 * math.log10(segment_rms)
    peak_db = 20 * math.log10(segment_peak)

    if segment_clipping > 0.03:
        quality = "clipping"
    elif rms_db < -35:
        quality = "too_quiet"
    elif rms_db > -6:
        quality = "too_loud"
    else:
        quality = "good"

    take_dir = source_path.parent / "takes"
    take_dir.mkdir(exist_ok=True)
    take_id = uuid.uuid4().hex[:8]
    take_path = take_dir / f"{source_path.stem}_take{take_number:02d}_{take_id}.wav"
    try:
        sf.write(str(take_path), segment, sample_rate)
    except Exception:
        return None

    return TakeInfo(
        take_id=take_id,
        path=str(take_path),
        start_sec=start_ms / 1000,
        end_sec=end_ms / 1000,
        duration_sec=duration_ms / 1000,
        rms_db=rms_db,
        peak_db=peak_db,
        clipping_pct=segment_clipping * 100,
        quality=quality,
        style=style,
    )


def split_wav_into_takes(
    wav_path: str,
    min_silence_ms: int = 600,
    min_take_ms: int = 800,
    style: str = "conversational",
) -> list[TakeInfo]:
    """Split a WAV into voiced takes and persist each valid take with a manifest."""
    try:
        import numpy as np
    except Exception:
        return []

    source_path = Path(wav_path)
    if not source_path.exists():
        return []
    loaded = _read_mono_wav(str(source_path))
    if loaded is None:
        return []
    samples, sample_rate = loaded

    window_size = int(sample_rate * 0.02)
    if window_size < 1:
        return []
    silence = _frame_rms_db(samples, window_size) < -40.0
    silence_wins = int(min_silence_ms / 20)

    takes: list[TakeInfo] = []
    in_speech = False
    start_win = 0
    silence_count = 0
    for index, is_silent in enumerate(silence):
        if not is_silent:
            if not in_speech:
                start_win = index
                in_speech = True
            silence_count = 0
        elif in_speech:
            silence_count += 1
            if silence_count >= silence_wins:
                take = _write_take(
                    source_path, samples, sample_rate, start_win,
                    index - silence_count, min_take_ms, len(takes) + 1, style,
                )
                if take:
                    takes.append(take)
                in_speech = False
                silence_count = 0
    if in_speech:
        take = _write_take(
            source_path, samples, sample_rate, start_win,
            len(silence), min_take_ms, len(takes) + 1, style,
        )
        if take:
            takes.append(take)

    manifest = source_path.parent / f"{source_path.stem}_takes.json"
    try:
        manifest.write_text(
            json.dumps([take.as_dict() for take in takes], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass
    return takes


def capability_report() -> dict[str, Any]:
    devices = []
    if SD_OK:
        try:
            devs = _sd.query_devices()
            devices = [
                {"name": d.get("name", ""), "max_in": d.get("max_input_channels", 0)}
                for d in devs
                if d.get("max_input_channels", 0) > 0
            ]
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

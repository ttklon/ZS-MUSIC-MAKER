# -*- coding: utf-8 -*-
"""
modules/voice_recording/takes.py — нарезка записи на дубли по паузам.

Energy-VAD с порогом относительно шумового пола: паузы ≥ `min_silence_ms`
разделяют дубли, слишком короткие фрагменты отбрасываются. Каждый дубль
получает метаданные (`take_id`, качество, стиль) и попадает в manifest.
"""

from __future__ import annotations

import json
import math
import uuid
from pathlib import Path
from typing import Any

from modules.voice_recording.state import LOGGER, TakeInfo


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
    except Exception as error:
        LOGGER.warning("voice take manifest was not written: %s", error)
    return takes

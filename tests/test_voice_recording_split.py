from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf

from modules.voice_recording import split_wav_into_takes


def test_split_wav_into_takes_persists_each_qualifying_voiced_region(tmp_path: Path) -> None:
    sample_rate = 8_000
    voice = np.full(sample_rate, 0.1, dtype=np.float32)
    silence = np.zeros(int(sample_rate * 0.7), dtype=np.float32)
    source = tmp_path / "phrase.wav"
    sf.write(source, np.concatenate((voice, silence, voice)), sample_rate)

    takes = split_wav_into_takes(
        str(source), min_silence_ms=600, min_take_ms=800, style="spoken",
    )

    assert len(takes) == 2
    assert all(take.quality == "good" for take in takes)
    assert all(take.style == "spoken" for take in takes)
    assert all(Path(take.path).is_file() for take in takes)
    assert all(take.duration_sec >= 0.8 for take in takes)

    manifest = source.with_name("phrase_takes.json")
    assert manifest.is_file()
    manifest_takes = json.loads(manifest.read_text(encoding="utf-8"))
    assert [entry["take_id"] for entry in manifest_takes] == [take.take_id for take in takes]

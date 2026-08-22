"""Generate deterministic, versioned audio fixtures for DSP regression tests."""

from __future__ import annotations

import random
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.beat_constructor import BeatConstructor
from modules.pro_audio_dsp import ProAudioDSP

FIXTURE_DIR = ROOT / "tests" / "fixtures" / "audio"


def golden_vocal_signal(sample_rate: int = 44_100, duration_sec: int = 10) -> np.ndarray:
    """Return a deterministic voiced synthetic vocal surrogate for spectral regression."""
    time = np.arange(sample_rate * duration_sec, dtype=np.float64) / sample_rate
    phrase = ((time % 2.5) < 1.65).astype(np.float64)
    attack = np.minimum(1.0, (time % 2.5) / 0.045)
    release = np.minimum(1.0, np.maximum(0.0, (1.65 - (time % 2.5)) / 0.12))
    envelope = phrase * np.minimum(attack, release)
    carrier = (
        0.10 * np.sin(2 * np.pi * 185 * time)
        + 0.045 * np.sin(2 * np.pi * 740 * time)
        + 0.020 * np.sin(2 * np.pi * 2200 * time)
        + 0.008 * np.sin(2 * np.pi * 6200 * time)
    )
    return (carrier * envelope).astype("float32")


def generate_goldens() -> dict[str, Path]:
    """Generate stable local DSP fixtures; Matchering remains an optional runtime."""
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    np.random.seed(20260822)
    random.seed(20260822)

    beat_path = FIXTURE_DIR / "golden_beat_15s.wav"
    with tempfile.TemporaryDirectory(prefix="zsmm_golden_") as tmp:
        result = BeatConstructor(
            bpm=130,
            groove={"hihat_density": 0.8, "swing": 0.1},
        ).build_track(
            duration_sec=15,
            include_intro=False,
            include_outro=False,
            out_name=str(beat_path),
        )
        generated_path = Path(result["beat_path"])
        if generated_path != beat_path:
            beat_path.write_bytes(generated_path.read_bytes())

    sr = 44_100
    duration_sec = 10
    time = np.arange(sr * duration_sec, dtype=np.float64) / sr
    raw = (
        0.045 * np.sin(2 * np.pi * 92 * time)
        + 0.020 * np.sin(2 * np.pi * 220 * time)
        + 0.006 * np.sin(2 * np.pi * 1740 * time)
    )
    raw_stereo = np.column_stack((raw, raw * 0.96 + 0.001 * np.sin(2 * np.pi * 0.7 * time)))
    master_path = FIXTURE_DIR / "golden_master_10s.wav"
    with tempfile.TemporaryDirectory(prefix="zsmm_golden_master_") as tmp:
        raw_path = Path(tmp) / "golden_raw.wav"
        sf.write(raw_path, raw_stereo, sr, subtype="PCM_24")
        result = ProAudioDSP.apply_mastering_chain(
            str(raw_path), str(master_path), target_lufs=-9.0
        )
        if not result.get("ok"):
            raise RuntimeError(f"Golden mastering failed: {result}")

    vocal_path = FIXTURE_DIR / "golden_vocal_10s.wav"
    sf.write(vocal_path, golden_vocal_signal(), sr, subtype="PCM_24")

    return {"beat": beat_path, "vocal": vocal_path, "master": master_path}


def main() -> int:
    for name, path in generate_goldens().items():
        data, sr = sf.read(path, always_2d=True)
        print(f"{name}: {path.relative_to(ROOT)} {data.shape[0] / sr:.3f}s {sr}Hz {data.shape[1]}ch")
    return 0


if __name__ == "__main__":
    from cli_contract import help_or_error

    if help_or_error(__doc__ or "ZS Music Maker tool"):
        raise SystemExit(0)
    raise SystemExit(main())

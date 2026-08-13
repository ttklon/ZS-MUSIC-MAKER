"""ZS Music Maker — финальная проверка качества трека.

v33 FIX (P2, SESSION_LOG v31.11): раньше здесь был жёстко зашит чужой путь
/home/ubuntu/ZS-MUSIC-MAKER/... — на любой другой машине инструмент всегда
печатал FAIL. Теперь путь берётся из argv[1]; без аргумента — ищем последний
masters/*.wav в output/; если и его нет — честный usage + exit 2.

Использование:
    python tools/validate_final_track.py [путь/к/track.wav]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.test_audio_quality import validate_audio_file
import soundfile as sf
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def _find_latest_master() -> Path | None:
    masters = sorted(ROOT.glob("output/**/masters/*.wav"))
    return masters[-1] if masters else None


def main() -> int:
    if len(sys.argv) > 1:
        track_path = Path(sys.argv[1])
    else:
        found = _find_latest_master()
        if not found:
            print("USAGE: python tools/validate_final_track.py <path/to/track.wav>")
            print("(мастера в output/**/masters/*.wav не найдены)")
            return 2
        track_path = found

    print(f"--- Final Quality Audit for: {track_path} ---")
    try:
        if not track_path.exists():
            raise FileNotFoundError(f"File not found: {track_path}")
        validate_audio_file(str(track_path))
        data, sr = sf.read(str(track_path))
        peak = float(np.max(np.abs(data)))
        rms = float(np.sqrt(np.mean(data**2)))
        duration = len(data) / sr
        channels = data.shape[1] if data.ndim > 1 else 1

        print("STATUS: PASS ✅")
        print(f"Peak Level: {peak:.4f} (Target <= 1.0)")
        print(f"RMS Level: {rms:.4f}")
        print(f"Duration: {duration:.2f}s")
        print(f"Sample Rate: {sr}Hz")
        print(f"Channels: {channels}")
        return 0
    except Exception as e:
        print("STATUS: FAIL ❌")
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

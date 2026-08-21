"""Run a compact truth check for honest RVC, mastering and MusicGen contracts."""

from __future__ import annotations

import struct
import sys
import tempfile
import wave
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def wav(path: Path) -> None:
    """Write one second of valid silent PCM audio for contract probes."""
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(8000)
        handle.writeframes(struct.pack("<8000h", *([0] * 8000)))


def main() -> int:
    """Execute truth contracts and return non-zero only on unexpected failures."""
    with tempfile.TemporaryDirectory() as directory:
        src = Path(directory) / "in.wav"
        wav(src)
        from modules import matchering_master, rvc_manager

        try:
            rvc_manager.infer(str(src), voice_name="definitely_missing")
        except RuntimeError as exc:
            print("RVC_HONEST_FAIL_PASS:", exc)
        else:
            print("RVC_FAIL: fallback still active")
            return 1
        out = Path(directory) / "master.wav"
        result = matchering_master.master_to_stand(str(src), str(out), "streaming")
        print("MASTER_RESULT:", result)
        from app.core import musicgen_texture

        music = musicgen_texture.generate_texture("test", duration_sec=1, vram_gb=0.0)
        print("MUSICGEN_RESULT:", music)
        from modules import master_pipeline_v12

        pipeline = master_pipeline_v12.run("api_test", {"references": []}, dry_run=True)
        print("PIPELINE_API:", pipeline.get("verdict"), pipeline.get("percent_ready"))
    return 0


if __name__ == "__main__":
    from cli_contract import help_or_error

    if help_or_error(__doc__ or "P0 truth test"):
        raise SystemExit(0)
    raise SystemExit(main())

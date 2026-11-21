"""Real CPU Silero download/inference, then cached offline inference. No audio mocks.

This checks Russian draft speech, NOT singing or a finished song. Intended for
GitHub-hosted Windows, where dependencies/network are installed explicitly.
"""
from __future__ import annotations

import json
import os
import platform
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "output" / "windows-neural-smoke"


def check_audio(path: Path) -> dict:
    import numpy as np
    import soundfile as sf

    audio, rate = sf.read(path, always_2d=True)
    if not audio.size or not np.isfinite(audio).all():
        raise ValueError("Empty or non-finite audio")
    peak = float(np.max(np.abs(audio)))
    seconds = len(audio) / rate
    if seconds < 0.5 or peak < 0.001:
        raise ValueError(f"Silent or too short: {seconds=}, {peak=}")
    return {"file": path.name, "seconds": seconds, "sample_rate": rate, "peak": peak}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"ok": False, "platform": platform.platform(), "python": sys.version,
              "kind": "real_neural_draft_speech_not_singing", "renders": []}
    try:
        import torch
        from modules.voice_synth import _synth_silero

        torch.set_num_threads(2)
        report["torch"] = torch.__version__
        for online, text in [(True, "Это настоящая проверка голосовой модели на компьютере с Windows."),
                             (False, "Вторая запись использует локальные веса без разрешения на скачивание.")]:
            os.environ["ZSMM_ONLINE"] = "1" if online else "0"
            target = OUT / ("online.wav" if online else "offline.wav")
            if not _synth_silero(text, str(target)):
                raise RuntimeError(f"Silero synthesis failed: {online=}; see workflow stderr")
            report["renders"].append({"online_allowed": online, **check_audio(target)})
        report["ok"] = True
        metrics = "; ".join(f"{r['file']}: {r['seconds']:.2f}s, peak={r['peak']:.4f}" for r in report["renders"])
        print("::notice title=Real neural speech passed::" + metrics)
    except Exception:
        report["error"] = traceback.format_exc()
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import numpy as np
import soundfile as sf

from modules import mastering_pro


def test_pedalboard_failure_does_not_disable_future_masters(tmp_path, monkeypatch) -> None:
    source = tmp_path / "source.wav"
    output = tmp_path / "master.wav"
    samples = np.column_stack((np.full(4096, 0.05), np.full(4096, -0.05)))
    sf.write(source, samples, 44_100)

    class FailingAudioFile:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            raise RuntimeError("temporary pedalboard failure")

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(mastering_pro, "HAS_PEDALBOARD", True)
    monkeypatch.setattr(mastering_pro, "HAS_PYLOUDNORM", False)
    monkeypatch.setattr(mastering_pro, "AudioFile", FailingAudioFile, raising=False)

    result = mastering_pro.process_mastering(str(source), str(output))

    assert result["ok"] is True
    assert result["engine"] == "numpy_rms_safe"
    assert output.exists()
    assert mastering_pro.HAS_PEDALBOARD is True

from __future__ import annotations

import numpy as np
import soundfile as sf

from modules.remix import render_remix


def test_remix_requires_source_authorization(tmp_path) -> None:
    result = render_remix("missing.wav", "missing.wav", str(tmp_path / "out.wav"))
    assert result["ok"] is False
    assert result["reason"] == "source vocal stem authorization is required"


def test_remix_mixes_authorized_stereo_vocal_once(tmp_path) -> None:
    sr = 8_000
    seconds = 2
    t = np.arange(sr * seconds) / sr
    beat = np.column_stack([0.15 * np.sin(2 * np.pi * 120 * t)] * 2)
    vocal = 0.08 * np.sin(2 * np.pi * 300 * t[:sr])
    beat_path = tmp_path / "beat.wav"
    vocal_path = tmp_path / "vocal.wav"
    out = tmp_path / "remix.wav"
    sf.write(beat_path, beat, sr)
    sf.write(vocal_path, vocal, sr)

    result = render_remix(str(beat_path), str(vocal_path), str(out), source_authorized=True)
    rendered, out_sr = sf.read(out, always_2d=True)

    assert result["ok"] is True
    assert result["vocal_frames_used"] == sr
    assert out_sr == sr
    assert rendered.shape == (sr * seconds, 2)
    assert np.max(np.abs(rendered)) <= 0.99

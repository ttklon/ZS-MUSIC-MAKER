"""Изоляция отказов мастеринга: один битый файл не ломает остальные стенды."""

from __future__ import annotations

import numpy as np
import soundfile as sf

from modules import mastering


def test_broken_input_returns_reason_instead_of_raising(tmp_path) -> None:
    broken = tmp_path / "broken.wav"
    broken.write_bytes(b"not a wav at all")

    result = mastering.master_one(str(broken), str(tmp_path / "out.wav"), stand="streaming")

    assert result["ok"] is False
    assert "read failed" in result["reason"]


def test_failed_stand_does_not_block_the_rest(tmp_path) -> None:
    source = tmp_path / "mix.wav"
    sample_rate = 44_100
    time = np.arange(sample_rate * 2) / sample_rate
    wave = 0.15 * np.sin(2 * np.pi * 220 * time)
    sf.write(source, np.stack([wave, wave * 0.9], axis=1), sample_rate)

    broken = tmp_path / "broken.wav"
    broken.write_bytes(b"broken")

    from modules import mastering as engine

    calls: list[str] = []
    original = engine.master_one

    def routed(mix_wav: str, out_wav: str, stand: str = "streaming"):
        calls.append(stand)
        if stand == "club":
            return {"ok": False, "reason": "synthetic club failure"}
        return original(mix_wav, out_wav, stand=stand)

    engine.master_one = routed  # type: ignore[assignment]
    try:
        result = engine.master_all_stands(str(source), str(tmp_path / "masters"), stands=["club", "streaming"])
    finally:
        engine.master_one = original  # type: ignore[assignment]

    assert calls == ["club", "streaming"]
    assert set(result["masters"]) == {"streaming"}
    assert result["summary"]["errors"]["club"] == "synthetic club failure"
    assert result["summary"]["gates_passed"] is False

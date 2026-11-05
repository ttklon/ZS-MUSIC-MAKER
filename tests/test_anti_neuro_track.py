"""Anti-neuro полировка трека обязана работать, а не падать в FALLBACK.

Регресс: в `_micro_timing_jitter` и соседних эффектах проверялось `np is None`,
хотя модуль импортирует numpy как `_np` — стадия всегда падала с NameError и
тихо отдавала копию мастера как «fallback».
"""

from __future__ import annotations

import numpy as np
import soundfile as sf

from modules import anti_neuro_track


def _master(tmp_path, name: str = "master.wav") -> str:
    sample_rate = 22_050
    time = np.arange(int(sample_rate * 3)) / sample_rate
    wave = 0.22 * np.sin(2 * np.pi * 110 * time) + 0.08 * np.sin(2 * np.pi * 660 * time)
    path = tmp_path / name
    sf.write(str(path), np.stack([wave, wave * 0.9], axis=1), sample_rate)
    return str(path)


def test_polish_track_runs_real_chain(tmp_path) -> None:
    source = _master(tmp_path)
    out = str(tmp_path / "polished.wav")

    result = anti_neuro_track.polish_track(source, out, preset="standard")

    assert result["ok"] is True
    assert len(result["stages_applied"]) >= 3
    assert "micro_timing_jitter" in " ".join(result["stages_applied"])

    samples, _ = sf.read(out, always_2d=True)
    assert samples.shape[1] == 2
    assert np.isfinite(samples).all()
    assert float(np.max(np.abs(samples))) <= 1.0


def test_polish_is_deterministic_for_seed(tmp_path) -> None:
    source = _master(tmp_path)
    first = str(tmp_path / "a.wav")
    second = str(tmp_path / "b.wav")

    anti_neuro_track.polish_track(source, first, preset="standard", seed=7)
    anti_neuro_track.polish_track(source, second, preset="standard", seed=7)

    a, _ = sf.read(first)
    b, _ = sf.read(second)
    assert np.allclose(a, b)


def test_missing_numpy_is_reported_not_faked(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(anti_neuro_track, "NP_OK", False)
    source = _master(tmp_path)

    result = anti_neuro_track.polish_track(source, str(tmp_path / "x.wav"))

    assert result["ok"] is False
    assert "soundfile" in result["error"]

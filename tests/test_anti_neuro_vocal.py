# -*- coding: utf-8 -*-
"""4.7: вокальная anti-neuro полировка — numpy-ветка без pydub, длина сохраняется."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from modules import anti_neuro

RATE = 32_000


def _vocal(seconds: float = 4.0) -> np.ndarray:
    time = np.arange(int(RATE * seconds)) / RATE
    envelope = np.zeros_like(time)
    for start, stop in ((0.2, 1.2), (1.6, 2.4), (2.8, 3.8)):
        envelope[(time >= start) & (time < stop)] = 1.0
    freq = 220.0 * 2.0 ** (8.0 * np.sin(2 * np.pi * 5.5 * time) / 1200.0)
    body = 0.2 * np.sin(2 * np.pi * np.cumsum(freq) / RATE) * envelope
    return np.stack([body, body * 0.95], axis=1)


def _write(tmp_path, audio: np.ndarray, name: str = "vocal.wav") -> str:
    path = tmp_path / name
    sf.write(str(path), audio.astype(np.float32), RATE)
    return str(path)


def test_no_pydub_or_ffmpeg_dependency() -> None:
    """На чистой Windows-машине нет ffmpeg: цепочка обязана работать без pydub."""
    import ast

    tree = ast.parse(Path(anti_neuro.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    assert "pydub" not in imported
    assert anti_neuro.capability_report()["ffmpeg_required"] is False


def test_polish_preserves_length_for_all_presets(tmp_path) -> None:
    audio = _vocal()
    source = _write(tmp_path, audio)

    for preset in ("gentle", "standard", "aggressive"):
        out = tmp_path / f"{preset}.wav"
        result = anti_neuro.polish_vocal(source, str(out), preset=preset, seed=5)

        assert result["ok"] is True, result
        assert result["length_preserved"] is True
        assert result["engine"] == "numpy_anti_neuro"
        assert result["stages_applied"]
        assert result["skipped"] == []
        assert sf.info(str(out)).frames == sf.info(source).frames


def test_polish_is_deterministic_with_seed(tmp_path) -> None:
    source = _write(tmp_path, _vocal())
    first = tmp_path / "first.wav"
    second = tmp_path / "second.wav"

    anti_neuro.polish_vocal(source, str(first), preset="standard", seed=11)
    anti_neuro.polish_vocal(source, str(second), preset="standard", seed=11)

    a, _ = sf.read(str(first))
    b, _ = sf.read(str(second))
    assert np.allclose(a, b)


def test_breaths_land_in_pauses_only(tmp_path) -> None:
    audio = _vocal()
    source = _write(tmp_path, audio)
    out = tmp_path / "polished.wav"

    result = anti_neuro.polish_vocal(source, str(out), preset="standard", seed=7)
    polished, _ = sf.read(str(out), always_2d=True)

    breaths = result["metrics"]["breaths_in_pauses"]["breaths"]
    assert breaths == 2
    # в начале файла (0–0.2 с) вдох не клеится: старый pydub-путь ломал таймлайн
    head_energy = float(np.sqrt(np.mean(polished[: int(RATE * 0.15)] ** 2)))
    assert head_energy < 1e-3
    # паузы 1.2–1.6 и 2.4–2.8 стали не тишиной
    for start, stop in ((1.25, 1.55), (2.45, 2.75)):
        pause = polished[int(RATE * start) : int(RATE * stop)]
        assert float(np.sqrt(np.mean(pause**2))) > 1e-4


def test_polish_reports_failure_honestly(tmp_path) -> None:
    result = anti_neuro.polish_vocal(str(tmp_path / "missing.wav"), str(tmp_path / "out.wav"))

    assert result["ok"] is False
    assert "read failed" in result["reason"]
    assert not (tmp_path / "out.wav").exists()


def test_apply_polish_maps_intensity_to_preset(tmp_path) -> None:
    source = _write(tmp_path, _vocal())
    quiet = anti_neuro.apply_polish(source, str(tmp_path / "q.wav"), intensity=0.1, seed=1)
    loud = anti_neuro.apply_polish(source, str(tmp_path / "l.wav"), intensity=0.9, seed=1)

    assert quiet["preset"] == "gentle"
    assert loud["preset"] == "aggressive"
    assert quiet["ok"] is True and loud["ok"] is True

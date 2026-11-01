"""4.5.4: референс-матчинг микса — профиль, коррекция, отчёт отклонений."""

from __future__ import annotations

import json

import numpy as np
import soundfile as sf

from modules.mix import reference as ref


def _signal(sample_rate: int = 22_050, seconds: float = 6.0, tilt: float = 0.0) -> np.ndarray:
    n = int(sample_rate * seconds)
    time = np.arange(n) / sample_rate
    rng = np.random.default_rng(4)
    base = 0.12 * np.sin(2 * np.pi * 90 * time) + 0.05 * rng.normal(0, 1, n)
    top = 0.02 * rng.normal(0, 1, n)
    treble = 10.0 ** (tilt / 20.0)
    return np.stack([base + top * treble, base * 0.9 + top * treble], axis=1)


def _write(tmp_path, name: str, audio: np.ndarray, sample_rate: int = 22_050) -> str:
    path = tmp_path / name
    sf.write(str(path), audio.astype(np.float32), sample_rate)
    return str(path)


def test_band_split_reconstructs_signal() -> None:
    audio = _signal()
    bands = ref._band_split(audio, 22_050)

    assert len(bands) == len(ref.BAND_EDGES_HZ) + 1
    assert np.allclose(np.sum(bands, axis=0), audio, atol=1e-9)


def test_band_gains_reconstruct_identity() -> None:
    audio = _signal()
    zeros = np.zeros(len(ref.BAND_EDGES_HZ) + 1)

    out = ref.apply_band_gains(audio, 22_050, zeros)

    assert np.allclose(out, audio, atol=1e-9)


def test_match_reduces_spectral_deviation(tmp_path) -> None:
    mix = _write(tmp_path, "mix.wav", _signal(tilt=0.0))
    # «Референс» ярче на 8 дБ в верхах и тише по низу
    reference = _write(tmp_path, "ref.wav", _signal(tilt=8.0))

    report = ref.match_to_reference(mix, reference, str(tmp_path / "matched.wav"))

    assert report["ok"] is True
    assert report["engine"] == "band_eq_match"
    before = report["bands"]["max_deviation_before_db"]
    after = report["bands"]["max_deviation_after_db"]
    assert after <= before
    assert after <= ref.GATE_DEVIATION_DB
    assert report["gates"]["true_peak"] is True
    assert report["gates"]["no_clipping"] is True


def test_match_writes_report_json(tmp_path) -> None:
    mix = _write(tmp_path, "mix.wav", _signal())
    reference = _write(tmp_path, "ref.wav", _signal(tilt=6.0))

    report = ref.match_to_reference(mix, reference, str(tmp_path / "out" / "matched.wav"))

    path = tmp_path / "out" / "reference_match_report.json"
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["bands"]["max_deviation_after_db"] <= ref.GATE_DEVIATION_DB
    assert "loudness" in payload and "crest_db" in payload


def test_missing_files_are_reported_honestly(tmp_path) -> None:
    report = ref.match_to_reference(str(tmp_path / "nope.wav"), str(tmp_path / "nope2.wav"))

    assert report["ok"] is False
    assert "not found" in report["reason"]


def test_matchering_failure_falls_back_and_is_marked(tmp_path, monkeypatch) -> None:
    mix = _write(tmp_path, "mix.wav", _signal())
    reference = _write(tmp_path, "ref.wav", _signal(tilt=4.0))

    monkeypatch.setattr(
        ref, "_match_with_matchering", lambda *args, **kwargs: {"ok": False, "reason": "synthetic failure"}
    )

    report = ref.match_to_reference(
        mix, reference, str(tmp_path / "matched.wav"), engine="matchering"
    )

    assert report["ok"] is True
    assert report["fallback_used"] is True
    assert "synthetic failure" in report["reason"]
    assert report["engine"] == "band_eq_match"

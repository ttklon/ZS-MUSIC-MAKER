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
    from modules.dsp.metrics import rms_dbfs
    assert np.allclose(ref.band_profile(audio, 22_050), [rms_dbfs(band) for band in bands])


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


def test_multiple_references_are_combined_equally_in_power(tmp_path):
    mix = _write(tmp_path, "mix.wav", _signal(tilt=0))
    a = _write(tmp_path, "a.wav", _signal(tilt=-3))
    b = _write(tmp_path, "b.wav", _signal(tilt=8))
    combined = ref.match_to_reference(mix, [a, b], str(tmp_path / "multi.wav"))
    reversed_order = ref.match_to_reference(mix, [b, a], str(tmp_path / "reverse.wav"))
    one = ref.match_to_reference(mix, a, str(tmp_path / "single.wav"))
    assert combined["ok"] and combined["references"] == [a, b]
    assert combined["reference_aggregation"] == "equal_weight_mean_power"
    assert combined["bands"]["reference_profile_db"] == reversed_order["bands"]["reference_profile_db"]
    assert combined["bands"]["reference_profile_db"] != one["bands"]["reference_profile_db"]


def test_different_sample_rates_compare_only_common_bandwidth(tmp_path):
    from scipy.signal import resample_poly
    mix = _write(tmp_path, "mix44.wav", _signal(sample_rate=44100, seconds=2), 44100)
    reference = _write(tmp_path, "ref8.wav", _signal(sample_rate=8000, seconds=2), 8000)
    result = ref.match_to_reference(mix, reference, str(tmp_path / "out.wav"))
    assert result["ok"] and result["analysis_sample_rate"] == 8000
    assert result["analysis_nyquist_hz"] == result["unassessed_above_hz"] == 4000
    assert result["gates"]["bandwidth_coverage"] is False
    assert result["gates_passed"] is False
    assert all(result["correction_db"][f"{f}Hz"] == 0 for f in [5120, 10240, 20000])
    data, _ = sf.read(mix, always_2d=True)
    expected = ref.band_profile(resample_poly(data, 80, 441, axis=0), 8000)
    assert list(result["bands"]["profile_before_db"].values()) == [round(float(x), 2) for x in expected]


def test_all_reference_inputs_required_and_never_overwritten(tmp_path):
    mix = _write(tmp_path, "mix.wav", _signal(seconds=2))
    existing = _write(tmp_path, "ref.wav", _signal(seconds=2, tilt=3))
    before = (tmp_path / "ref.wav").read_bytes()
    result = ref.match_to_reference(mix, [existing, str(tmp_path / "missing.wav")], str(tmp_path / "out.wav"))
    assert result["ok"] is False and "reference not found" in result["reason"]
    assert not (tmp_path / "out.wav").exists()
    result = ref.match_to_reference(mix, existing, existing)
    assert result["ok"] is False and "overwrite" in result["reason"]
    assert (tmp_path / "ref.wav").read_bytes() == before
    assert not ref.match_to_reference(mix, [existing, existing], engine="matchering")["ok"]


def test_silent_and_multichannel_reference_is_not_silently_accepted(tmp_path):
    mix = _write(tmp_path, "mix.wav", _signal(seconds=2))
    silent = _write(tmp_path, "silent.wav", np.zeros((44100, 2)))
    assert "silent reference" in ref.match_to_reference(mix, silent)["reason"]
    surround = _write(tmp_path, "surround.wav", np.zeros((44100, 4)))
    assert "channel count" in ref.match_to_reference(mix, surround)["reason"]


def test_reference_report_measures_encoded_output(tmp_path):
    from modules.dsp.metrics import true_peak_dbtp, clipping_samples
    mix = _write(tmp_path, "mix.wav", _signal(tilt=0))
    reference = _write(tmp_path, "ref.wav", _signal(tilt=5))
    result = ref.match_to_reference(mix, reference, str(tmp_path / "matched.wav"))
    written, sr = sf.read(result["out_wav"], always_2d=True)
    actual = ref.band_profile(written, sr)
    assert list(result["bands"]["profile_after_db"].values()) == [round(float(x), 2) for x in actual]
    assert result["gates"]["true_peak"] == (true_peak_dbtp(written) <= -1.0)
    assert result["gates"]["no_clipping"] == (clipping_samples(written) == 0)


def test_matchering_changed_rate_fails_instead_of_changing_playback_speed(tmp_path, monkeypatch):
    mix = _write(tmp_path, "mix.wav", _signal(seconds=2))
    reference = _write(tmp_path, "ref.wav", _signal(seconds=2))
    def fake_matchering(mix, reference, output):
        sf.write(output, np.zeros((8000, 2)), 8000)
        return {"ok": True, "engine": "matchering"}
    monkeypatch.setattr(ref, "_match_with_matchering", fake_matchering)
    result = ref.match_to_reference(mix, reference, str(tmp_path / "out.wav"), engine="matchering")
    assert not result["ok"] and "sample rate" in result["reason"]
    assert not ref.match_to_reference(mix, reference, engine="matchering", strength=.5)["ok"]


def test_hardlinked_output_cannot_overwrite_input(tmp_path):
    import os
    import pytest
    mix = _write(tmp_path, "mix.wav", _signal(seconds=2))
    reference = _write(tmp_path, "ref.wav", _signal(seconds=2))
    linked = tmp_path / "linked.wav"
    before = (tmp_path / "ref.wav").read_bytes()
    try:
        os.link(reference, linked)
    except OSError:
        pytest.skip("hard links unavailable")
    result = ref.match_to_reference(mix, reference, str(linked))
    assert not result["ok"] and "overwrite" in result["reason"]
    assert (tmp_path / "ref.wav").read_bytes() == before

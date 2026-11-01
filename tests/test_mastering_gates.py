"""Гейты мастеринга (§7.2): −1 dBTP, LUFS по стендам, отчёт и совместимость."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf

from modules import mastering
from modules.dsp import metrics


def _mix(sample_rate: int = 22_050, seconds: float = 8.0) -> np.ndarray:
    n = int(sample_rate * seconds)
    time = np.arange(n) / sample_rate
    rng = np.random.default_rng(5)
    low = 0.16 * np.sin(2 * np.pi * 55 * time)
    mid = 0.10 * np.sin(2 * np.pi * 220 * time)
    high = 0.04 * np.sin(2 * np.pi * 3000 * time)
    width = 0.08 * rng.normal(0, 1, n)
    left = low + mid + high + width
    right = low + mid + high * 0.7 - width
    return np.stack([left, right], axis=1)


def _write(tmp_path: Path, audio: np.ndarray, sample_rate: int = 22_050) -> str:
    path = tmp_path / "mix.wav"
    sf.write(str(path), audio.astype(np.float32), sample_rate)
    return str(path)


def test_streaming_master_hits_lufs_target_and_true_peak(tmp_path) -> None:
    mix = _write(tmp_path, _mix())

    result = mastering.master_one(mix, str(tmp_path / "master.wav"), stand="streaming")

    assert result["ok"] is True
    assert result["gates"]["true_peak"] is True
    assert result["gates"]["no_clipping"] is True
    assert result["gates"]["lufs"] is True, result["report"]
    assert abs(result["output_lufs"] + 14.0) <= 0.5
    assert result["output_true_peak_dbtp"] <= -1.0
    assert Path(result["path"]).exists()


def test_mastered_file_is_stereo_and_within_gates(tmp_path) -> None:
    mix = _write(tmp_path, _mix())
    out = tmp_path / "master.wav"

    mastering.master_one(mix, str(out), stand="headphones")

    samples, sample_rate = sf.read(str(out), always_2d=True)
    report = metrics.loudness_report(samples, sample_rate)
    assert report["channels"] == 2
    assert report["true_peak_dbtp"] <= -1.0
    assert report["clipping_samples"] == 0
    assert 0.2 <= report["stereo_correlation"] <= 0.8


def test_all_stands_write_report_with_gate_details(tmp_path) -> None:
    mix = _write(tmp_path, _mix())

    result = mastering.master_all_stands(mix, str(tmp_path / "masters"), stands=["streaming", "tiktok"])

    assert result["ok"] is True
    assert set(result["masters"]) == {"streaming", "tiktok"}
    report_path = Path(result["report_path"])
    assert report_path.exists()
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert set(payload["gates"]) == {"streaming", "tiktok"}
    assert payload["standards"]["streaming"] == -14.0
    for stand_report in payload["reports"].values():
        assert stand_report["true_peak_dbtp"] <= -1.0


def test_loud_stand_reports_advice_instead_of_fake_success(tmp_path) -> None:
    """−8.5 LUFS на динамичном миксе не выдаётся за успех: есть совет и факт."""
    quiet = _mix(seconds=4.0) * 0.05
    mix = _write(tmp_path, quiet)

    result = mastering.master_one(mix, str(tmp_path / "club.wav"), stand="club")

    assert result["output_true_peak_dbtp"] <= -1.0
    if not result["gates"]["lufs"]:
        assert result["advice"]
        assert "недостижима" in result["advice"]


def test_normalize_master_loudness_keeps_ceiling(tmp_path) -> None:
    source = tmp_path / "loud_source.wav"
    sample_rate = 22_050
    time = np.arange(sample_rate * 3) / sample_rate
    wave = 0.9 * np.sin(2 * np.pi * 220 * time)
    sf.write(str(source), np.stack([wave, wave], axis=1), sample_rate)

    result = mastering.normalize_master_loudness(str(source), str(source), target_lufs=-14.0)

    assert result["ok"] is True
    assert result["output_true_peak_dbtp"] <= -1.0
    assert result["output_peak_db"] <= -1.0

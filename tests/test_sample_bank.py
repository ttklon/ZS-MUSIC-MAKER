# -*- coding: utf-8 -*-
"""
Гейты сэмплового банка: лицензии, velocity-слои, round-robin, честный статус.

Главная проверка здесь — не «функция прочитала JSON», а то, что
**неклированный сэмпл не попадает в бит**, а синтез отчитывается как FALLBACK.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf

from app.audio.samples import (
    ALLOWED_LICENSES,
    capability,
    load_bank,
    pitch_shift,
    read_sample,
    time_stretch,
    validate_manifest,
)
from modules.beat_constructor import BeatConstructor


def _write_sample(path: Path, freq: float = 60.0, seconds: float = 0.12, sr: int = 44_100) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    time_axis = np.arange(int(sr * seconds)) / sr
    sf.write(path, 0.8 * np.sin(2 * np.pi * freq * time_axis), sr)
    return str(path)


def _manifest(tmp_path: Path, rows: dict) -> Path:
    payload = {"schema": "zsmm.sample-bank.v1", "instruments": rows}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_empty_bank_reports_fallback_honestly(tmp_path) -> None:
    bank = load_bank(tmp_path / "missing.json")
    report = capability(bank)

    assert bank.empty is True
    assert report["status"] == "FALLBACK"
    assert report["total_samples"] == 0
    assert report["instruments_on_synth"], "должен быть список инструментов на синтезе"
    assert any("no sample manifest" in warning for warning in bank.warnings)


def test_licensed_samples_are_accepted_with_velocity_layers(tmp_path) -> None:
    kick_dir = tmp_path / "kick"
    rows = []
    for index, velocity in enumerate((0.4, 0.7, 1.0)):
        rows.append(
            {
                "file": f"kick/kick_{index}.wav",
                "license": "CC0-1.0",
                "source": "https://example.org/pack",
                "velocity": velocity,
                "round_robin": index,
            }
        )
        _write_sample(tmp_path / "kick" / f"kick_{index}.wav", 60.0 + index)
    _write_sample(kick_dir / "kick_0.wav", 60.0)
    bank = load_bank(_manifest(tmp_path, {"kick": rows}))

    usable = bank.usable("kick")
    assert len(usable) == 3
    assert {round(entry.velocity, 2) for entry in usable} == {0.4, 0.7, 1.0}
    assert bank.choose("kick", velocity=0.72).velocity == 0.7, "должен браться ближайший слой"


def test_unlicensed_sample_is_rejected_and_never_used(tmp_path) -> None:
    _write_sample(tmp_path / "kick" / "bad.wav")
    manifest = _manifest(
        tmp_path,
        {
            "kick": [
                {"file": "kick/bad.wav", "license": "ALL-RIGHTS-RESERVED", "source": "https://x/y"}
            ]
        },
    )
    bank = load_bank(manifest)

    assert bank.usable("kick") == []
    assert bank.entries["kick"][0].problems
    assert capability(bank)["status"] == "FALLBACK"
    assert "ALL-RIGHTS-RESERVED" not in ALLOWED_LICENSES


def test_missing_file_and_hash_mismatch_are_flagged(tmp_path) -> None:
    _write_sample(tmp_path / "kick" / "k.wav")
    manifest = _manifest(
        tmp_path,
        {
            "kick": [
                {"file": "kick/absent.wav", "license": "CC0-1.0", "source": "https://x"},
                {
                    "file": "kick/k.wav",
                    "license": "CC0-1.0",
                    "source": "https://x",
                    "sha256": "0" * 64,
                },
            ]
        },
    )
    bank = load_bank(manifest, verify_hash=True)

    problems = [entry.problems for entry in bank.entries["kick"]]
    assert ["file missing"] in problems
    assert any("sha256 mismatch" in item for item in problems[1])


def test_manifest_schema_validation_names_problems() -> None:
    problems = validate_manifest({"schema": "wrong", "instruments": {"kick": [{"license": "CC0"}]}})

    assert any("schema must be" in problem for problem in problems)
    assert any("no 'file'" in problem for problem in problems)


def test_read_sample_resamples_to_requested_rate(tmp_path) -> None:
    path = _write_sample(tmp_path / "k.wav", seconds=0.5, sr=8_000)
    audio = read_sample(path, sample_rate=44_100)

    assert audio is not None
    assert abs(len(audio) / 44_100 - 0.5) < 0.02
    assert np.max(np.abs(audio)) > 0.5


def test_pitch_shift_changes_length_and_keeps_signal() -> None:
    audio = read_sample(_write_sample(Path("/tmp") / "zs_pitch_src.wav", seconds=0.2))
    up = pitch_shift(audio, 12.0)

    assert up is not None and len(up) < len(audio) * 0.6
    assert np.max(np.abs(up)) > 0.5


def test_time_stretch_keeps_duration_ratio() -> None:
    audio = read_sample(_write_sample(Path("/tmp") / "zs_stretch_src.wav", seconds=0.4))
    stretched = time_stretch(audio, 1.5)

    assert stretched is not None
    assert 1.3 <= len(stretched) / len(audio) <= 1.7


def test_constructor_reports_fallback_when_bank_is_empty(monkeypatch) -> None:
    from app.audio import samples as samples_module

    monkeypatch.setattr(samples_module, "load_bank", lambda *a, **k: samples_module.SampleBank())
    np.random.seed(5)
    constructor = BeatConstructor(bpm=128, genre="phonk", groove={"hihat_density": 0.0}, seed=5)

    report = constructor._drum_engine_report()

    assert report["status"] == "FALLBACK"
    assert "0 of 6" in report["reason"]
    assert report["sample_bank"]["total_samples"] == 0


def test_samples_audit_tool_reports_licenses_and_coverage(tmp_path, monkeypatch) -> None:
    from tools import samples_audit

    _write_sample(tmp_path / "kick" / "k.wav")
    manifest = _manifest(
        tmp_path,
        {
            "kick": [
                {
                    "file": "kick/k.wav",
                    "license": "CC0-1.0",
                    "source": "https://example.org",
                    "velocity": 1.0,
                }
            ]
        },
    )
    monkeypatch.setattr(samples_audit, "load_bank", lambda *a, **k: load_bank(manifest, verify_hash=True))
    monkeypatch.setattr(samples_audit, "REPORT_PATH", tmp_path / "audit.json")

    report = samples_audit.audit(min_layers=3, min_variants=2)
    licenses = samples_audit.licenses_text(report)

    assert report["n_samples"] == 1
    assert report["rejected"] == []
    assert report["coverage"]["kick"]["samples"] == 1
    assert "kick" in report["instruments_thin"], "один слой — это «тонко», аудит обязан сказать"
    assert "CC0-1.0" in licenses and "example.org" in licenses

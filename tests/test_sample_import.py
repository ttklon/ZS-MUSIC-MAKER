# -*- coding: utf-8 -*-
"""Банк сэмплов: импорт CC0-паков, аудит и реальное использование в бите.

Три вещи, которые легко «сломать молча» и потому проверяются здесь:

1. `tools/import_samples.py` собирает банк детерминированно (повторный
   прогон даёт тот же манифест и те же SHA-256) и выбрасывает дубли;
2. аудит не требует фальшивых velocity-слоёв от драм-машины и не считает
   отсутствие синтезируемых инструментов блокером;
3. движок бита действительно берёт удары из банка и честно называет движок.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from tools import import_samples

ROOT = Path(__file__).resolve().parents[1]


def _write_pack(source: Path) -> Path:
    """Мини-пак с тем же расположением файлов, что у настоящих источников."""
    rng = np.random.default_rng(3)
    layout = {
        "bd8/BD0050.WAV": 55.0,
        "bd8/BD0010.WAV": 45.0,
        "bd8/BD0025.WAV": 60.0,
        "bd8/BD2550.WAV": 70.0,
        "sd8/SD7550.WAV": 200.0,
        "sd8/SD5010.WAV": 180.0,
        "sd8/SD2500.WAV": 160.0,
        "cp8/CP.WAV": 300.0,
        "ch8/CH.WAV": 9000.0,
        "oh8/OH00.WAV": 8000.0,
        "oh8/OH25.WAV": 8000.0,
        "oh8/OH50.WAV": 8000.0,
        "drum-samples/01-hard-trap/kicks/hard-kick-01.wav": 50.0,
        "drum-samples/01-hard-trap/kicks/hard-kick-02.wav": 52.0,
        "drum-samples/01-hard-trap/snares/hard-snare-01.wav": 190.0,
        "drum-samples/01-hard-trap/snares/hard-snare-02.wav": 195.0,
        "drum-samples/01-hard-trap/claps/clap-01.wav": 320.0,
        "drum-samples/01-hard-trap/hi-hats/hi-hat-closed-01.wav": 8800.0,
        "drum-samples/01-hard-trap/open-hats/open-hat-01.wav": 7800.0,
        "drum-samples/01-hard-trap/808s/808-bass-sub.wav": 48.0,
        "drum-samples/01-hard-trap/808s/808-bass-dist.wav": 50.0,
        "drum-samples/02-bounce/kicks/bounce-kick-01.wav": 58.0,
        "drum-samples/02-bounce/kicks/bounce-kick-03.wav": 62.0,
        "drum-samples/02-bounce/snares/bounce-snare-01.wav": 170.0,
        "drum-samples/02-bounce/snares/bounce-snare-03.wav": 175.0,
        "drum-samples/02-bounce/claps/clap-01.wav": 330.0,
        "drum-samples/02-bounce/open-hats/open-hat-01.wav": 7700.0,
        "drum-samples/02-bounce/808s/808-bass-long.wav": 46.0,
        "drum-samples/03-soulful-vintage/kicks/vintage-kick-01.wav": 54.0,
        "drum-samples/03-soulful-vintage/kicks/vintage-kick-02.wav": 56.0,
        "drum-samples/03-soulful-vintage/snares/vintage-snare-01.wav": 165.0,
        "drum-samples/03-soulful-vintage/snares/vintage-snare-02.wav": 168.0,
        "drum-samples/03-soulful-vintage/claps/vintage-clap-01.wav": 310.0,
        "drum-samples/03-soulful-vintage/808s/808-bass-lofi.wav": 47.0,
    }
    sr = 44_100
    for relative, freq in layout.items():
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        t = np.arange(int(sr * 0.5)) / sr
        decay = np.exp(-t * 8.0)
        tone = np.sin(2 * np.pi * freq * t) * decay
        noise = rng.standard_normal(t.size) * decay * 0.1
        sf.write(str(path), (tone + noise).astype(np.float32), sr)
    return source


def test_fundamental_detection_finds_bass_drum_tone() -> None:
    sr = 44_100
    t = np.arange(int(sr * 0.6)) / sr
    tone = np.sin(2 * np.pi * 55.0 * t) * np.exp(-t * 3.0)
    detected = import_samples.fundamental_hz(tone, sr)
    assert 52.0 <= detected <= 58.0, detected


def test_prepare_normalises_to_mono_44k_and_peak_below_one(tmp_path: Path) -> None:
    source = tmp_path / "loud.wav"
    sr = 48_000
    t = np.arange(sr) / sr
    stereo = np.stack([np.sin(2 * np.pi * 100 * t)] * 2, axis=1) * 3.0  # клиппинг на входе
    sf.write(str(source), stereo, sr)

    target = tmp_path / "out" / "kick.wav"
    stats = import_samples.prepare(source, target)

    data, rate = sf.read(str(target), always_2d=True)
    assert rate == 44_100
    assert data.shape[1] == 1, "банк держим в моно — стерео задаёт движок"
    assert np.max(np.abs(data)) <= 0.9
    assert stats["duration_sec"] > 0.5


def test_import_is_deterministic_and_drops_duplicates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pack = _write_pack(tmp_path / "src")
    out_dir = tmp_path / "samples"
    monkeypatch.setattr(import_samples, "SAMPLES_DIR", out_dir)
    monkeypatch.setattr(import_samples, "MANIFEST_PATH", out_dir / "manifest.json")
    monkeypatch.setattr(import_samples, "ATTRIBUTION_PATH", out_dir / "ATTRIBUTION.md")

    first = import_samples.build_manifest(pack)["manifest"]
    second = import_samples.build_manifest(pack)["manifest"]

    assert first == second, "повторный импорт обязан давать тот же манифест"
    files = [row["file"] for rows in first["instruments"].values() for row in rows]
    assert len(files) == len(set(files))
    hashes = [row["sha256"] for rows in first["instruments"].values() for row in rows]
    assert len(hashes) == len(set(hashes)), "один и тот же звук не должен попасть дважды"


def test_manifest_covers_drum_engine_instruments(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pack = _write_pack(tmp_path / "src")
    monkeypatch.setattr(import_samples, "SAMPLES_DIR", tmp_path / "samples")
    manifest = import_samples.build_manifest(pack)["manifest"]
    for name in ("kick", "snare", "clap", "hat", "open_hat", "808"):
        assert manifest["instruments"].get(name), f"нет сэмплов для {name}"
    assert manifest["velocity_mode"] == "engine-gain"
    for row in manifest["instruments"]["kick"]:
        assert row["license"] == "CC0-1.0" and row["source"].startswith("https://")
        assert 20.0 <= row["tuning_hz"] <= 200.0


def test_shipped_bank_is_audit_clean() -> None:
    """Тот банк, что лежит в репозитории, обязан проходить собственный аудит."""
    from tools import samples_audit

    report = samples_audit.audit()
    assert report["rejected"] == []
    assert report["instruments_missing"] == []
    assert report["ok"] is True, report["instruments_thin"]
    assert report["n_samples"] >= 30


def test_audit_requires_real_layers_when_bank_declares_them(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Если банк обещает слои, аудит обязан их требовать."""
    from app.audio.samples import load_bank
    from tools import samples_audit

    sample = tmp_path / "kick" / "k.wav"
    sample.parent.mkdir(parents=True)
    sf.write(str(sample), np.zeros(1000, dtype=np.float32), 22_050)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": "zsmm.sample-bank.v1",
                "velocity_mode": "layers",
                "instruments": {
                    "kick": [{"file": "kick/k.wav", "license": "CC0-1.0", "source": "x", "velocity": 1.0}],
                    "snare": [{"file": "kick/k.wav", "license": "CC0-1.0", "source": "x"}],
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(samples_audit, "load_bank", lambda *a, **k: load_bank(manifest))
    report = samples_audit.audit()
    assert "kick" in report["instruments_thin"]
    assert report["velocity_mode"] == "layers"


def test_beat_engine_reports_bank_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    """Движок бита обязан признаться, что удары — из банка."""
    from modules.beat.constructor import BeatConstructor

    report = BeatConstructor(bpm=140, genre="trap", groove={}, seed=3)._drum_engine_report()
    assert report["status"] == "REAL_PASS"
    assert report["engine"] == "sample_bank+procedural"
    assert {"kick", "snare", "clap", "hat", "open_hat", "808"} <= set(
        report["sample_bank"]["instruments_with_samples"]
    )


def test_bank_clap_is_used_without_explicit_sample_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    from modules.beat.constructor import BeatConstructor

    beat = BeatConstructor(bpm=140, genre="trap", groove={}, seed=3)
    beat.slot_patterns["snare"][4] = 1
    requested: list[str] = []

    def bank_audio(instrument: str, velocity: float) -> np.ndarray:
        requested.append(instrument)
        return np.ones(100, dtype=np.float32)

    monkeypatch.setattr(beat, "_bank_audio", bank_audio)
    beat._generate_snare(4, 1)
    assert requested == ["clap"]
    beat._generate_snare(4, 0)
    assert requested[-1] == "snare"


def test_808_sample_attack_fades_before_end(monkeypatch: pytest.MonkeyPatch) -> None:
    from modules.beat.constructor import BeatConstructor
    from modules.beat import drums

    beat = BeatConstructor(bpm=140, genre="trap", groove={}, seed=3)
    beat.slot_patterns["bass"] = [1] + [0] * 15
    monkeypatch.setattr(beat, "_bank_audio", lambda *args: np.ones(beat.sr, dtype=np.float32))
    monkeypatch.setattr(beat, "_hit_offset_sec", lambda *args: 0.0)
    monkeypatch.setattr(beat, "_velocity", lambda *args, **kwargs: 1.0)
    monkeypatch.setattr(drums, "synth_808", lambda sr, freq, dur, *args, **kwargs: np.zeros(int(sr * dur), dtype=np.float32))
    audio = beat._generate_bass_line(0, beat.sr * 2)
    last = int(beat.sr * 0.09) - 1
    assert audio[last - 441] > 0
    assert audio[last] == pytest.approx(0, abs=1e-7)
    assert audio[last + 1] == pytest.approx(0, abs=1e-7)

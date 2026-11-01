"""Гейты микса (§7.2): staging −18 dBFS, ширина, сайдчейн, отчёт."""

from __future__ import annotations

import json

import numpy as np
import soundfile as sf

from modules.dsp import metrics
from modules.mix import bus as mix_bus
from modules.mix.staging import stage


def _beat(sample_rate: int = 22_050, seconds: float = 8.0) -> np.ndarray:
    """Простой «бит»: кик на каждом такте + шумная широкая подложка."""
    n = int(sample_rate * seconds)
    time = np.arange(n) / sample_rate
    rng = np.random.default_rng(11)
    music = 0.12 * np.sin(2 * np.pi * 110 * time) + 0.05 * rng.normal(0, 1, n)
    kick_period = int(sample_rate * 0.5)
    for start in range(0, n, kick_period):
        length = min(int(sample_rate * 0.18), n - start)
        env = np.exp(-np.arange(length) / (sample_rate * 0.05))
        music[start : start + length] += 0.6 * np.sin(
            2 * np.pi * 55 * np.arange(length) / sample_rate
        ) * env
    # Правая сторона заметно отличается по фазе/уровню: иначе «микс» монофоничен,
    # и коридор корреляции 0.2…0.8 недостижим без искусственного расширения.
    other = 0.12 * np.sin(2 * np.pi * 110 * time + 0.9) + 0.05 * rng.normal(0, 1, n)
    stereo = np.stack([music, 0.7 * other], axis=1)
    return stereo


def _vocal(sample_rate: int = 22_050, seconds: float = 8.0) -> np.ndarray:
    n = int(sample_rate * seconds)
    time = np.arange(n) / sample_rate
    phrase = 0.18 * np.sin(2 * np.pi * 180 * time) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.9 * time))
    return np.stack([phrase, phrase], axis=1)


def _write(tmp_path, name: str, audio: np.ndarray, sample_rate: int = 22_050):
    path = tmp_path / name
    sf.write(str(path), audio.astype(np.float32), sample_rate)
    return str(path)


def test_gain_staging_hits_minus_18_reference(tmp_path) -> None:
    audio = _beat()
    staged, report = stage(audio, sample_rate=22_050)

    # Либо цель достигнута, либо пик упёрся в потолок — но потолок соблюдён.
    assert report["target_met"] or report["limited_by_peak"]
    assert metrics.reference_rms_dbfs(staged, 22_050) <= -17.5
    assert metrics.peak_dbfs(staged) <= -3.0 + 0.05


def test_build_mix_passes_all_gates(tmp_path) -> None:
    beat = _write(tmp_path, "beat.wav", _beat())
    vocal = _write(tmp_path, "vocal.wav", _vocal())

    result = mix_bus.build_mix(beat, vocal, str(tmp_path / "mix.wav"))

    assert result["vocal_used"] is True
    assert result["gates_passed"] is True, result["gates"]
    report = result["report"]
    assert -19.0 <= report["reference_rms_dbfs"] <= -17.0
    assert 0.2 <= report["stereo_correlation"] <= 0.8
    assert report["true_peak_dbtp"] <= -1.0
    assert report["clipping_samples"] == 0
    assert 8.0 <= report["reference_crest_db"] <= 14.0


def test_build_mix_without_vocal_is_honestly_instrumental(tmp_path) -> None:
    beat = _write(tmp_path, "beat.wav", _beat())
    missing = str(tmp_path / "no_such_vocal.wav")

    result = mix_bus.build_mix(beat, missing, str(tmp_path / "mix.wav"))

    assert result["vocal_used"] is False
    assert result["gates"]["true_peak"] is True


def test_sidechain_ducks_low_band_but_keeps_the_kick() -> None:
    from modules.dsp.filters import low_band
    from modules.dsp.metrics import rms_dbfs
    from modules.mix.ducking import duck_low_band

    sample_rate = 22_050
    beat = _beat(sample_rate)
    out, report = duck_low_band(beat, beat, sample_rate, depth_db=3.0)

    assert report["applied"] is True
    assert report["duck_depth_db"] >= 1.0
    assert report["kick_peak_retention"] >= 0.4
    # Верх не тронут: изменился только низ (проверяем полосой выше 1 кГц,
    # чтобы не ловить утечку НЧ-фильтра на срезе 120 Гц).
    from modules.dsp.filters import highpass

    high_before = highpass(beat, sample_rate, 1000.0)
    high_after = highpass(out, sample_rate, 1000.0)
    assert abs(rms_dbfs(high_before) - rms_dbfs(high_after)) <= 0.01


def test_width_matching_respects_the_corridor() -> None:
    from modules.mix.width import match_width

    n = 41_000
    rng = np.random.default_rng(17)
    time = np.arange(n) / 22_050
    mid = np.sin(2 * np.pi * 200 * time)
    side = 0.18 * rng.normal(0, 1, n)
    skewed = np.stack([mid + side, mid - side], axis=1)
    assert metrics.stereo_correlation(skewed) > 0.85

    out, report = match_width(skewed)

    assert 0.2 <= report["correlation_after"] <= 0.8
    assert report["matched"] is True
    assert metrics.mono_loss_db(out) <= 3.0


def test_width_cannot_invent_stereo_from_mono() -> None:
    from modules.mix.width import match_width

    mono = np.stack([np.sin(2 * np.pi * 200 * np.arange(22_050) / 22_050)] * 2, axis=1)
    out, report = match_width(mono)

    assert report["matched"] is False
    assert "mono source" in report["reason"]
    assert np.allclose(out, mono)


def test_prepare_mix_writes_report_json(tmp_path) -> None:
    beat = _write(tmp_path, "beat.wav", _beat())
    vocal = _write(tmp_path, "vocal.wav", _vocal())

    result = mix_bus.prepare_mix(beat, vocal, tmp_path / "out")

    report_path = tmp_path / "out" / "mix_report.json"
    assert report_path.exists()
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["gates"] == result["gates"]
    assert payload["sidechain"]["cut_hz"] == 120.0

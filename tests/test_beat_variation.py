"""План 4.7: микро-вариативность повторов, дрейф темпа, шум комнаты, энтропия."""

from __future__ import annotations

import numpy as np

from modules.beat import microtime, variation


def _click_track(bars: int, sample_rate: int = 8_000, bar_sec: float = 1.0, vary: bool = False):
    """Простой трек из тактов: одинаковые клики или с развитием."""
    bar_samples = int(bar_sec * sample_rate)
    audio = np.zeros((bar_samples * bars, 2), dtype=np.float32)
    for bar in range(bars):
        for hit, step in enumerate((0, 4, 8, 12)):
            start = bar * bar_samples + int(step * bar_samples / 16)
            length = min(200, audio.shape[0] - start)
            amplitude = 0.8 if step == 0 else 0.5
            if vary:
                amplitude *= 0.7 + 0.1 * ((bar + hit) % 5)
            audio[start : start + length, 0] += amplitude * np.hanning(length)
            audio[start : start + length, 1] += amplitude * 0.9 * np.hanning(length)
    return audio, sample_rate


def test_repetition_entropy_flags_identical_bars():
    audio, sample_rate = _click_track(bars=16, vary=False)

    report = variation.repetition_report(audio, sample_rate, bpm=240.0)

    assert report["bars"] == 16
    assert report["entropy_normalized"] <= 0.35
    assert report["formulaic"] is True
    assert report["bar_similarity"] > 0.95


def test_repetition_entropy_accepts_varied_bars():
    audio, sample_rate = _click_track(bars=16, vary=True)

    report = variation.repetition_report(audio, sample_rate, bpm=240.0)

    assert report["distinct_types"] >= 2
    assert report["entropy_normalized"] > 0.0
    assert report["bar_similarity"] < 0.99


def test_bar_variant_is_deterministic_and_protects_anchors():
    def draw(seed: int):
        rng = np.random.default_rng(seed)
        return [
            variation.bar_variant(
                lambda: float(rng.random()), lambda a, b: float(rng.uniform(a, b)), bar, "hook"
            )
            for bar in range(32)
        ]

    first = draw(7)
    second = draw(7)

    assert first == second
    for variant in first:
        assert not set(variant["skip_hat_steps"]) & set(range(0, 16, 4))
        assert len(variant["skip_hat_steps"]) <= 1
        assert -0.4 <= variant["bar_gain_db"] <= 0.2


def test_tempo_drift_preserves_length_and_is_bounded():
    sample_rate = 8_000
    time = np.arange(sample_rate * 20) / sample_rate
    audio = np.stack([np.sin(2 * np.pi * 220 * time)] * 2, axis=1)

    drifted, info = microtime.tempo_drift(audio, sample_rate, amount_pct=0.2)

    assert drifted.shape == audio.shape
    assert info["drift_pct"] == 0.2
    assert info["peak_deviation_ms"] > 0.0
    assert not np.allclose(drifted, audio)


def test_zero_drift_is_identity():
    audio = np.random.default_rng(0).normal(0, 0.1, (4_000, 2))
    drifted, info = microtime.tempo_drift(audio, 8_000, amount_pct=0.0)

    assert info["drift_pct"] == 0.0
    assert np.allclose(drifted, audio)


def test_room_noise_sets_measurable_floor():
    sample_rate = 8_000
    silence = np.zeros((sample_rate * 5, 2))

    noisy, info = microtime.add_room_noise(silence, sample_rate, level_dbfs=-62.0, seed=1)

    rms = float(np.sqrt(np.mean(noisy**2)))
    rms_db = 20.0 * np.log10(max(rms, 1e-12))
    assert info["noise_dbfs"] == -62.0
    assert abs(rms_db + 62.0) <= 1.0


def test_apply_humanity_reports_both_layers():
    sample_rate = 8_000
    audio = np.zeros((sample_rate * 3, 2)) + 0.1
    result, report = microtime.apply_humanity(audio, sample_rate, seed=3)

    assert result.shape == audio.shape
    assert report["tempo_drift"]["drift_pct"] == microtime.DEFAULT_DRIFT_PCT
    assert report["room_noise"]["noise_dbfs"] == microtime.DEFAULT_NOISE_DBFS
    assert 0.0 < report["peak"] <= 1.0


def test_built_beat_is_not_formulaic_and_has_humanity(tmp_path, monkeypatch):
    from modules.beat_constructor import BeatConstructor

    monkeypatch.setattr("modules.beat.paths.output_dir", lambda: str(tmp_path))
    result = BeatConstructor(genre="drift phonk", bpm=128, seed=5).build_track(
        duration_sec=40, out_name="human.wav"
    )

    repetition = result["repetition"]
    assert repetition["formulaic"] is False, repetition
    assert repetition["entropy_normalized"] >= variation.MIN_ENTROPY
    humanity = result["humanity"]
    assert humanity["tempo_drift"]["drift_pct"] == 0.2
    assert humanity["room_noise"]["noise_dbfs"] == -62.0

# -*- coding: utf-8 -*-
"""`modules/anti_neuro_track.py`: каждый эффект «оживления» и честные отказы.

Стадия вызывается из `app/core/stages/master.py`, то есть работает на каждом
прогоне. Базовые тесты покрывали только «цепочка не падает»; здесь проверяется
поведение каждого эффекта: что он делает с сигналом, что не портит форму,
что одинаков при одном `seed` и что отказ называется, а не превращается в
трейсбек.

Про звук утверждений нет: измеряется форма сигнала (пик, длина, NaN), а не то,
«звучит ли живее».
"""

from __future__ import annotations

import numpy as np
import pytest
import soundfile as sf

from modules import anti_neuro_track as ant

SR = 22050


def _stereo(path=None, seconds: float = 3.0, freq: float = 220.0):
    t = np.arange(int(SR * seconds)) / SR
    wave = 0.3 * np.sin(2 * np.pi * freq * t)
    y = np.stack([wave, wave * 0.8], axis=1).astype("float32")
    return (y, SR) if path is None else _write(path, y)


def _write(path, y):
    sf.write(str(path), y, SR)
    return str(path)


# --------------------------------------------------------------------------- #
#  Отказы
# --------------------------------------------------------------------------- #

def test_unreadable_file_is_refused_not_raised(tmp_path) -> None:
    """Битый вход — это `ok: False` с причиной, а не `LibsndfileError`."""
    broken = tmp_path / "broken.wav"
    broken.write_bytes("это не wav вовсе".encode("utf-8"))

    result = ant.polish_track(str(broken), str(tmp_path / "out.wav"))

    assert result["ok"] is False
    assert "cannot read" in result["error"]
    assert str(broken) in result["error"]
    assert not (tmp_path / "out.wav").exists()


def test_unknown_preset_is_refused_with_reason(tmp_path) -> None:
    source = _write(tmp_path / "in.wav", _stereo()[0])

    result = ant.polish_track(source, str(tmp_path / "out.wav"), preset="loud")

    assert result["ok"] is False
    assert "loud" in result["error"]
    assert "gentle" in result["error"], "отказ перечисляет допустимые значения"


def test_missing_input_path_is_refused(tmp_path) -> None:
    result = ant.polish_track(str(tmp_path / "nope.wav"), str(tmp_path / "out.wav"))

    assert result["ok"] is False and "cannot read" in result["error"]


# --------------------------------------------------------------------------- #
#  Пресеты
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("preset", ["gentle", "standard", "aggressive"])
def test_every_preset_produces_finite_audio(tmp_path, preset) -> None:
    source = _write(tmp_path / "in.wav", _stereo()[0])
    out = str(tmp_path / f"{preset}.wav")

    result = ant.polish_track(source, out, preset=preset, seed=3)

    samples, sr = sf.read(out, always_2d=True)
    assert result["ok"] is True and result["preset"] == preset
    assert sr == SR
    assert np.isfinite(samples).all()
    assert float(np.max(np.abs(samples))) <= 1.0
    assert samples.shape[0] == int(SR * 3.0)


def test_aggressive_applies_more_stages_than_gentle(tmp_path) -> None:
    source = _write(tmp_path / "in.wav", _stereo()[0])

    gentle = ant.polish_track(source, str(tmp_path / "g.wav"), preset="gentle")
    aggressive = ant.polish_track(source, str(tmp_path / "a.wav"), preset="aggressive")

    assert "ghost_harmonies_kill" not in " ".join(gentle["stages_applied"])
    assert "formulaic_structure_bust" in " ".join(aggressive["stages_applied"])
    assert "imperfect_tuning" in " ".join(gentle["stages_applied"])


def test_preset_jitter_amount_is_reported(tmp_path) -> None:
    source = _write(tmp_path / "in.wav", _stereo()[0])

    gentle = ant.polish_track(source, str(tmp_path / "g.wav"), preset="gentle")
    aggressive = ant.polish_track(source, str(tmp_path / "a.wav"), preset="aggressive")

    assert "micro_timing_jitter(2.5ms)" in gentle["stages_applied"]
    assert "micro_timing_jitter(8.0ms)" in aggressive["stages_applied"]


# --------------------------------------------------------------------------- #
#  Отдельные эффекты
# --------------------------------------------------------------------------- #

def test_jitter_keeps_length_and_peak_below_limit() -> None:
    y, sr = _stereo()

    out = ant._micro_timing_jitter(y, sr, amount_ms=5.0, seed=1)

    assert out.shape == y.shape
    assert float(np.max(np.abs(out))) <= 0.99


def test_jitter_is_deterministic_for_seed() -> None:
    y, sr = _stereo()

    a = ant._micro_timing_jitter(y, sr, amount_ms=5.0, seed=11)
    b = ant._micro_timing_jitter(y, sr, amount_ms=5.0, seed=11)

    assert np.array_equal(a, b)


def test_zero_jitter_returns_input_untouched() -> None:
    y, sr = _stereo()

    assert ant._micro_timing_jitter(y, sr, amount_ms=0.0) is y


def test_breath_insert_adds_energy_only_at_positions() -> None:
    y, sr = _stereo(seconds=1.0)
    breath = [np.full(int(sr * 0.1), 0.05, dtype="float32")]
    quiet = np.zeros_like(y)

    out = ant._breath_insert(quiet, sr, breath, [0.2], volume_db=-6.0)

    start = int(0.2 * sr)
    assert float(np.max(np.abs(out[start : start + 100]))) > 0.0
    assert float(np.max(np.abs(out[: start - 10]))) == 0.0


def test_breath_ignores_positions_past_the_end() -> None:
    y, sr = _stereo(seconds=0.5)
    breath = [np.full(100, 0.05, dtype="float32")]

    out = ant._breath_insert(y.copy(), sr, breath, [10.0])

    assert np.array_equal(out, y)


def test_breath_without_samples_is_noop() -> None:
    y, sr = _stereo()

    assert ant._breath_insert(y, sr, [], [0.5]) is y


def test_section_variation_only_touches_listed_sections() -> None:
    y, sr = _stereo(seconds=4.0)
    sections = [{"start_sec": 1.0, "end_sec": 2.0, "energy": 0.3}]

    out = ant._section_dynamics_variation(y.copy(), sr, sections, seed=5)

    assert not np.array_equal(out[int(1.0 * sr) : int(2.0 * sr)], y[int(1.0 * sr) : int(2.0 * sr)])
    assert np.array_equal(out[: int(0.9 * sr)], y[: int(0.9 * sr)])


def test_section_variation_skips_invalid_ranges() -> None:
    y, sr = _stereo(seconds=2.0)

    out = ant._section_dynamics_variation(
        y.copy(), sr, [{"start_sec": 1.5, "end_sec": 1.0}, {"start_sec": 99.0, "end_sec": 100.0}],
        seed=1,
    )

    assert np.array_equal(out, y)


def test_section_variation_stronger_for_quiet_sections() -> None:
    """Замысел: тихие секции получают больший разброс по громкости."""
    y, sr = _stereo(seconds=4.0)
    loud = [{"start_sec": 0.0, "end_sec": 1.0, "energy": 0.9}]
    quiet = [{"start_sec": 0.0, "end_sec": 1.0, "energy": 0.2}]

    gains = []
    for sections in (loud, quiet):
        out = ant._section_dynamics_variation(y.copy(), sr, sections, seed=2)
        gains.append(float(np.mean(np.abs(out[:sr])) / np.mean(np.abs(y[:sr]))))
    assert abs(gains[1] - 1.0) >= abs(gains[0] - 1.0) - 0.02


def test_ghost_kill_attenuates_the_notch_frequency() -> None:
    """Нотч на 3.2 кГц обязан ослабить именно эту частоту."""
    sr = 44100
    t = np.arange(sr * 2) / sr
    whistle = 0.3 * np.sin(2 * np.pi * 3200 * t)
    y = np.stack([whistle, whistle], axis=1).astype("float32")

    out = ant._ghost_harmonies_kill(y, sr)

    rms_in = float(np.sqrt(np.mean(y ** 2)))
    rms_out = float(np.sqrt(np.mean(out ** 2)))
    assert rms_out < rms_in * 0.5


def test_ghost_kill_keeps_other_frequencies() -> None:
    sr = 44100
    t = np.arange(sr * 2) / sr
    body = 0.3 * np.sin(2 * np.pi * 200 * t)
    y = np.stack([body, body], axis=1).astype("float32")

    out = ant._ghost_harmonies_kill(y, sr)

    assert float(np.sqrt(np.mean(out ** 2))) > float(np.sqrt(np.mean(y ** 2))) * 0.9


def test_structure_bust_is_skipped_for_short_tracks() -> None:
    y, sr = _stereo(seconds=10.0)

    assert ant._formulaic_structure_bust(y, sr, seed=1) is y


def test_structure_bust_quiets_a_slice_of_long_track() -> None:
    y, sr = _stereo(seconds=40.0)

    out = ant._formulaic_structure_bust(y.copy(), sr, seed=4)

    ratios = [
        float(np.mean(np.abs(out[i : i + 500])) / (np.mean(np.abs(y[i : i + 500])) + 1e-9))
        for i in range(0, len(y) - 500, 500)
    ]
    assert min(ratios) < 0.5, "должен появиться провал (drop)"
    assert max(ratios) > 0.9, "остальной трек не должен пострадать"


def test_tape_saturation_is_bounded() -> None:
    y, sr = _stereo()
    hot = y * 3.0

    out = ant._tape_saturation(hot, amount=0.09)

    assert np.isfinite(out).all()
    assert float(np.max(np.abs(out))) < float(np.max(np.abs(hot)))


def test_lofi_pass_limits_high_frequencies() -> None:
    sr = 22050
    t = np.arange(sr) / sr
    high = 0.3 * np.sin(2 * np.pi * 9000 * t)
    y = np.stack([high, high], axis=1).astype("float32")

    out = ant._lofi_pass(y, sr, cutoff=15000.0)

    assert float(np.sqrt(np.mean(out ** 2))) < float(np.sqrt(np.mean(y ** 2))) * 0.6


def test_lofi_pass_survives_low_sample_rate() -> None:
    """На низком sr фильтр не должен падать: срез ограничен 0.45 Найквиста."""
    sr = 8000
    t = np.arange(sr) / sr
    y = (0.3 * np.sin(2 * np.pi * 200 * t)).astype("float32")

    out = ant._lofi_pass(y, sr, cutoff=15000.0)

    assert np.isfinite(out).all()


def test_imperfect_tuning_keeps_level() -> None:
    y, sr = _stereo()

    out = ant._imperfect_tuning(y.copy(), sr, cents=4.0)

    assert out.shape == y.shape
    assert np.isfinite(out).all()
    assert float(np.sqrt(np.mean(out ** 2))) == pytest.approx(
        float(np.sqrt(np.mean(y ** 2))), rel=0.1
    )


# --------------------------------------------------------------------------- #
#  Разметка из аранжировки
# --------------------------------------------------------------------------- #

def test_arrangement_marks_verse_and_chorus_positions(tmp_path, monkeypatch) -> None:
    source = _write(tmp_path / "in.wav", _stereo()[0])
    seen: dict = {}

    def fake_breath(y, sr, samples, positions, volume_db=-22.0):
        seen["positions"] = list(positions)
        seen["volume_db"] = volume_db
        return y

    monkeypatch.setattr(ant, "_breath_insert", fake_breath)
    plan = {"sections": [
        {"name": "intro", "start_sec": 0.0},
        {"name": "verse1", "start_sec": 7.4},
        {"name": "chorus", "start_sec": 22.1},
        {"name": "outro", "start_sec": 100.0},
    ]}

    ant.polish_track(source, str(tmp_path / "out.wav"), arrangement_plan=plan,
                     breath_samples=[np.zeros(100, dtype="float32")])

    assert seen["positions"] == [7.45, 22.150000000000002]
    assert seen["volume_db"] == -24.0


def test_mono_track_is_supported(tmp_path) -> None:
    t = np.arange(int(SR * 2)) / SR
    mono = (0.3 * np.sin(2 * np.pi * 220 * t)).astype("float32")
    source = str(tmp_path / "mono.wav")
    sf.write(source, mono, SR)

    result = ant.polish_track(source, str(tmp_path / "out.wav"), preset="standard", seed=1)

    samples, _ = sf.read(str(tmp_path / "out.wav"))
    assert result["ok"] is True
    assert samples.ndim == 1
    assert np.isfinite(samples).all()


# --------------------------------------------------------------------------- #
#  Деградация без scipy и без numpy
# --------------------------------------------------------------------------- #

def test_effects_degrade_gracefully_without_scipy(monkeypatch) -> None:
    """Нет scipy — эффекты не падают, а возвращают вход без изменений."""
    import sys

    monkeypatch.setitem(sys.modules, "scipy", None)
    monkeypatch.setitem(sys.modules, "scipy.signal", None)
    monkeypatch.setitem(sys.modules, "scipy.interpolate", None)
    y, sr = _stereo(seconds=1.0)

    assert ant._ghost_harmonies_kill(y, sr) is y
    assert ant._imperfect_tuning(y, sr) is y
    assert ant._lofi_pass(y, sr) is y


def test_effects_are_noop_without_numpy(monkeypatch) -> None:
    monkeypatch.setattr(ant, "NP_OK", False)
    y, sr = _stereo(seconds=1.0)

    assert ant._micro_timing_jitter(y, sr) is y
    assert ant._breath_insert(y, sr, [], []) is y
    assert ant._section_dynamics_variation(y, sr, []) is y
    assert ant._ghost_harmonies_kill(y, sr) is y
    assert ant._formulaic_structure_bust(y, sr) is y
    assert ant._tape_saturation(y) is y
    assert ant._imperfect_tuning(y, sr) is y
    assert ant._lofi_pass(y, sr) is y
    assert ant._read_track("any.wav") == (None, None)


def test_mono_effects_work_on_one_dimensional_audio() -> None:
    t = np.arange(int(SR * 1.0)) / SR
    y = (0.3 * np.sin(2 * np.pi * 220 * t)).astype("float32")
    sr = SR

    assert ant._ghost_harmonies_kill(y, sr).ndim == 1
    assert ant._imperfect_tuning(y, sr).ndim == 1
    assert ant._lofi_pass(y, sr).ndim == 1


def test_breath_on_mono_and_on_multichannel() -> None:
    t = np.arange(int(SR * 1.0)) / SR
    mono = (0.1 * np.sin(2 * np.pi * 220 * t)).astype("float32")
    breath = [np.full(int(SR * 0.05), 0.05, dtype="float32")]

    out_mono = ant._breath_insert(mono.copy(), SR, breath, [0.1])
    assert float(np.max(np.abs(out_mono))) > float(np.max(np.abs(mono)))

    three = np.stack([mono, mono, mono], axis=1)
    out_three = ant._breath_insert(three.copy(), SR, breath, [0.1])
    assert out_three.shape == three.shape
    assert float(np.mean(np.abs(out_three[:, 2]))) == pytest.approx(
        float(np.mean(np.abs(three[:, 2]))), rel=0.2
    ), "третьего канала в эффекте нет — он остаётся почти как был"


def test_mono_section_variation_and_structure_bust() -> None:
    t = np.arange(int(SR * 40)) / SR
    y = (0.3 * np.sin(2 * np.pi * 220 * t)).astype("float32")

    out = ant._section_dynamics_variation(
        y.copy(), SR, [{"start_sec": 1.0, "end_sec": 2.0, "energy": 0.2}], seed=1
    )
    busted = ant._formulaic_structure_bust(y.copy(), SR, seed=2)

    assert out.ndim == 1 and np.isfinite(out).all()
    assert busted.ndim == 1 and np.isfinite(busted).all()


def test_write_creates_parent_directory(tmp_path) -> None:
    y, sr = _stereo(seconds=0.5)
    target = tmp_path / "nested" / "deep" / "out.wav"

    ant._write_track(str(target), y, sr)

    assert target.is_file()


def test_lofi_cutoff_is_clamped_for_tiny_sample_rate() -> None:
    """Очень низкий sr: срез прижимается к 0.45 Найквиста, без ValueError."""
    sr = 2000
    t = np.arange(sr) / sr
    y = (0.3 * np.sin(2 * np.pi * 100 * t)).astype("float32")

    out = ant._lofi_pass(y, sr, cutoff=15000.0)

    assert np.isfinite(out).all()


def test_no_clipping_limit_is_engaged_only_above_threshold() -> None:
    """Ветки «пик > 0.99» против «пик в норме» проверяются обе."""
    sr = SR
    t = np.arange(sr) / sr
    quiet = np.stack([0.2 * np.sin(2 * np.pi * 220 * t)] * 2, axis=1).astype("float32")
    out_quiet = ant._micro_timing_jitter(quiet, sr, amount_ms=5.0, seed=1)
    assert float(np.max(np.abs(out_quiet))) <= 0.99

    # сигнал у самого предела: без ограничения наложение блоков даёт > 1.0
    loud = quiet * 5.0
    out_loud = ant._micro_timing_jitter(loud, sr, amount_ms=8.0, seed=1)
    assert float(np.max(np.abs(out_loud))) <= 0.99


def test_none_breath_sample_is_skipped() -> None:
    y, sr = _stereo(seconds=0.5)

    out = ant._breath_insert(y.copy(), sr, [None, None], [0.1])

    assert np.array_equal(out, y)


def test_ghost_kill_skips_frequencies_above_nyquist() -> None:
    """На sr 6 кГц (Найквист 3 кГц) все нотчи выше предела — сигнал не тронут."""
    sr = 6000
    t = np.arange(sr) / sr
    y = np.stack([0.3 * np.sin(2 * np.pi * 300 * t)] * 2, axis=1).astype("float32")

    out = ant._ghost_harmonies_kill(y, sr)

    assert np.allclose(out, y)


def test_structure_bust_handles_drop_at_the_very_end(monkeypatch) -> None:
    """Провал у края файла не должен давать пустой срез."""
    import random as random_module

    class EdgeRandom(random_module.Random):
        def uniform(self, a, b):
            return 0.999  # t у самого конца

        def randint(self, a, b):
            return 1

    monkeypatch.setattr(ant, "random", type("R", (), {"Random": EdgeRandom}))
    sr = SR
    t = np.arange(sr * 40) / sr
    y = (0.3 * np.sin(2 * np.pi * 220 * t)).astype("float32")

    out = ant._formulaic_structure_bust(y.copy(), sr, seed=1)

    assert np.isfinite(out).all()

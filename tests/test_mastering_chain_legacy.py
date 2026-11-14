# -*- coding: utf-8 -*-
"""`modules/mastering_chain.py`: тонкий legacy-адаптер над единым мастерингом.

Модуль не покрыт ни одним тестом (`smoke_god` дергает его как отдельный
инструмент, но не в наборе). Держим два обещания из docstring: адаптер остаётся
тонким (никакой второй DSP-реализации) и не прячет отказы — если микс с вокалом
не удался, это видно в логе, а мастер всё равно собирается из сухого бита.

`modules.mastering` подменяется: проверяется логика адаптера, а не лимитер.
Сам мастеринг меряется в `tests/test_dsp_metrics.py` и `smoke_audio`.
"""

from __future__ import annotations

import logging
import sys
import types
from pathlib import Path

import numpy as np
import soundfile as sf

import modules as modules_pkg

from modules import mastering_chain

SR = 8000


def _wav(path: Path, value: float = 0.2) -> str:
    t = np.arange(int(SR * 0.4)) / SR
    sf.write(path, value * np.sin(2 * np.pi * 220 * t), SR)
    return str(path)


def _fake_mastering(monkeypatch, *, lufs: float = -14.0, ok: bool = True) -> dict:
    calls: dict = {"master_one": [], "normalize": [], "mix": []}

    def master_one(src, dst, stand="streaming"):
        calls["master_one"].append((src, dst, stand))
        Path(dst).write_bytes(b"RIFF" + b"\0" * 4096)
        return {
            "ok": ok,
            "engine": "numpy_true_peak_limiter",
            "output_lufs": lufs,
            "input_rms_dbfs": -20.0,
            "output_rms_dbfs": -12.0,
            "reason": "" if ok else "limiter missing",
        }

    def normalize(src, dst=None, target_lufs=-14.0, ceiling_db=-1.0):
        calls["normalize"].append((src, dst, target_lufs, ceiling_db))
        return {"ok": True, "output_lufs": target_lufs}

    fake = types.SimpleNamespace(master_one=master_one, normalize_master_loudness=normalize)
    # `from modules import mastering` берёт атрибут пакета, а не sys.modules —
    # подменять надо оба, иначе тест получает настоящий движок.
    monkeypatch.setitem(sys.modules, "modules.mastering", fake)
    monkeypatch.setattr(modules_pkg, "mastering", fake, raising=False)
    return calls


# --------------------------------------------------------------------------- #
#  process_mastering
# --------------------------------------------------------------------------- #

def test_missing_input_is_refused_with_reason(tmp_path) -> None:
    result = mastering_chain.process_mastering(
        str(tmp_path / "nope.wav"), str(tmp_path / "out.wav")
    )

    assert result["ok"] is False
    assert "input wav not found" in result["reason"]


def test_mastering_failure_is_not_disguised(tmp_path, monkeypatch) -> None:
    _fake_mastering(monkeypatch, ok=False)
    source = _wav(tmp_path / "in.wav")

    result = mastering_chain.process_mastering(source, str(tmp_path / "out.wav"))

    assert result["ok"] is False
    assert result["reason"] == "limiter missing"


def test_master_without_vocal_goes_straight_to_engine(tmp_path, monkeypatch) -> None:
    calls = _fake_mastering(monkeypatch)
    source = _wav(tmp_path / "in.wav")
    target = str(tmp_path / "out.wav")

    result = mastering_chain.process_mastering(source, target)

    assert calls["master_one"] == [(source, target, "streaming")]
    assert calls["normalize"] == [], "громкость уже в цели — доводить нечего"
    assert result["ok"] is True
    assert result["engine"] == "numpy_true_peak_limiter"
    assert result["applied_gain"] == 8.0
    assert result["channels"] == 2


def test_loudness_off_target_is_corrected(tmp_path, monkeypatch) -> None:
    calls = _fake_mastering(monkeypatch, lufs=-11.0)
    target = str(tmp_path / "out.wav")

    mastering_chain.process_mastering(_wav(tmp_path / "in.wav"), target, target_lufs=-14.0)

    assert len(calls["normalize"]) == 1
    assert calls["normalize"][0][2] == -14.0


def test_within_tolerance_is_not_touched(tmp_path, monkeypatch) -> None:
    """Отклонение 0.2 LUFS — не повод перелимитировать трек заново."""
    calls = _fake_mastering(monkeypatch, lufs=-14.2)

    mastering_chain.process_mastering(_wav(tmp_path / "in.wav"), str(tmp_path / "out.wav"))

    assert calls["normalize"] == []


def test_vocal_is_mixed_before_mastering(tmp_path, monkeypatch) -> None:
    calls = _fake_mastering(monkeypatch)
    beat = _wav(tmp_path / "beat.wav")
    vocal = _wav(tmp_path / "vocal.wav")
    mixed: list = []
    fake_bus = types.SimpleNamespace(
        build_mix=lambda a, b, out: mixed.append((a, b, out)) or {"ok": True, "gates_passed": True}
    )
    monkeypatch.setitem(sys.modules, "modules.mix.bus", fake_bus)
    monkeypatch.setitem(sys.modules, "modules.mix", types.SimpleNamespace(bus=fake_bus))

    mastering_chain.process_mastering(beat, str(tmp_path / "out.wav"), vocal_path=vocal)

    assert len(mixed) == 1
    assert mixed[0][0] == beat and mixed[0][1] == vocal
    assert mixed[0][2].endswith("_legacy_mix.wav")
    assert calls["master_one"][0][0] == mixed[0][2]


def test_failed_vocal_mix_is_logged_and_dry_beat_used(tmp_path, monkeypatch, caplog) -> None:
    """Отказ микса виден в логе: мастер уйдёт из сухого бита, и это не сюрприз."""
    calls = _fake_mastering(monkeypatch)
    beat = _wav(tmp_path / "beat.wav")
    fake_bus = types.SimpleNamespace(build_mix=lambda *a, **k: {"ok": False, "reason": "no vocal"})
    monkeypatch.setitem(sys.modules, "modules.mix.bus", fake_bus)
    monkeypatch.setitem(sys.modules, "modules.mix", types.SimpleNamespace(bus=fake_bus))

    with caplog.at_level(logging.WARNING, logger="modules.mastering_chain"):
        mastering_chain.process_mastering(
            beat, str(tmp_path / "out.wav"), vocal_path=_wav(tmp_path / "vocal.wav")
        )

    assert "legacy master mix failed" in caplog.text
    assert calls["master_one"][0][0] == beat


def test_failed_mix_gates_are_reported(tmp_path, monkeypatch, caplog) -> None:
    calls = _fake_mastering(monkeypatch)
    fake_bus = types.SimpleNamespace(build_mix=lambda *a, **k: {
        "ok": True, "gates_passed": False, "gates": {"true_peak": False}})
    monkeypatch.setitem(sys.modules, "modules.mix.bus", fake_bus)
    monkeypatch.setitem(sys.modules, "modules.mix", types.SimpleNamespace(bus=fake_bus))

    with caplog.at_level(logging.WARNING, logger="modules.mastering_chain"):
        mastering_chain.process_mastering(
            _wav(tmp_path / "beat.wav"), str(tmp_path / "out.wav"),
            vocal_path=_wav(tmp_path / "vocal.wav"),
        )

    assert "gates failed" in caplog.text


def test_missing_vocal_file_falls_back_to_dry_beat(tmp_path, monkeypatch) -> None:
    calls = _fake_mastering(monkeypatch)
    beat = _wav(tmp_path / "beat.wav")

    mastering_chain.process_mastering(
        beat, str(tmp_path / "out.wav"), vocal_path=str(tmp_path / "gone.wav")
    )

    assert calls["master_one"][0][0] == beat


def test_normalize_is_reexported_from_engine(tmp_path, monkeypatch) -> None:
    calls = _fake_mastering(monkeypatch)

    result = mastering_chain.normalize_master_loudness(
        "in.wav", "out.wav", target_lufs=-9.0, ceiling_db=-1.2
    )

    assert result["ok"] is True
    assert calls["normalize"] == [("in.wav", "out.wav", -9.0, -1.2)]


def test_public_api_is_only_two_functions() -> None:
    """Тонкий адаптер: расширение `__all__` — сигнал, что сюда снова тащат DSP."""
    assert set(mastering_chain.__all__) == {"normalize_master_loudness", "process_mastering"}


def test_module_has_no_own_dsp_imports() -> None:
    """Вторая реализация мастеринга не должна вернуться в этот файл."""
    source = (Path(__file__).resolve().parents[1] / "modules" / "mastering_chain.py").read_text(
        encoding="utf-8"
    )
    for forbidden in ("import pedalboard", "import pyloudnorm", "from pedalboard"):
        assert forbidden not in source

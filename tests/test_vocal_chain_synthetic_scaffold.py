# -*- coding: utf-8 -*-
"""Синтетический каркас вокала: не тратить работу и не рапортовать успех.

Найдено на реальном прогоне `tools/smoke_god.py`. TTS в окружении нет, стадия
`_stage_voice_synth` честно выдавала numpy-каркас с `synthetic: true`, RVC был
заблокирован, и `_run_vocal_chain` затем выбрасывал каркас
(`vocal_final = None`) — но **после** этого гонял полный вокальный DSP:
деэссер, дабл, 9 throw-дублей. В отчёте при этом стояло
`_stage_vocal_fx: ok=true, engine=numpy_vocal_fx`, хотя микс честно писал
`vocal_used=false`.

То есть работа делалась впустую, а отчёт выглядел так, будто эффекты попали в
трек. Тесты держат два правила: (1) бесполезная обработка не запускается,
(2) отчёт называет её так, как есть.

Подмена `_stage_vocal_fx` — это запись факта вызова, а не проверка звука:
реальные эффекты проверяются в `tests/test_voice_stage_chain.py`.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from app.core.stages import vocal_chain

SR = 8000


def _wav(path: Path, seconds: float = 0.5) -> str:
    t = np.arange(int(SR * seconds)) / SR
    sf.write(path, 0.2 * np.sin(2 * np.pi * 200 * t), SR)
    return str(path)


def _recipe(**overrides) -> dict:
    base = {
        "voice_mode": "pro",
        "own_vocal_wav": None,
        "use_rvc": True,
        "use_vocal_fx": True,
        "tune": False,
    }
    base.update(overrides)
    return base


def _patch_synth(monkeypatch, payload: dict) -> None:
    monkeypatch.setattr(vocal_chain, "_stage_voice_synth", lambda *_a, **_k: payload)


def _patch_rvc(monkeypatch, payload: dict) -> None:
    monkeypatch.setattr(vocal_chain, "_stage_rvc", lambda *_a, **_k: payload)


def _by_name(stages: list) -> dict:
    return {stage.name: stage for stage in stages}


# --------------------------------------------------------------------------- #
#  Бесполезная обработка не запускается
# --------------------------------------------------------------------------- #

def test_synthetic_scaffold_without_rvc_does_not_run_vocal_fx(
    tmp_path, monkeypatch
) -> None:
    scaffold = _wav(tmp_path / "scaffold.wav")
    _patch_synth(monkeypatch, {
        "ok": True, "path": scaffold, "engine": "rap_scaffold_numpy_v22",
        "synthetic": True, "blocked": True,
    })
    _patch_rvc(monkeypatch, {"ok": True, "blocked": True, "path": "",
                             "reason": "upstream synthetic; RVC BLOCKED (P0.05)"})
    calls: list = []
    monkeypatch.setattr(
        vocal_chain, "_stage_vocal_fx",
        lambda *a, **k: calls.append((a, k)) or {"ok": True, "path": scaffold},
    )

    stages, vocal_final, warnings = vocal_chain._run_vocal_chain(
        _recipe(), "строка", tmp_path
    )

    assert calls == [], "обработка каркаса, который не попадёт в микс, — впустую"
    assert vocal_final is None
    fx = _by_name(stages)["_stage_vocal_fx"]
    assert fx.status.value == "BLOCKED"
    assert "synthetic" in fx.reason
    assert any("synthetic scaffold not mixed" in warning for warning in warnings)


def test_blocked_vocal_fx_names_the_real_reason(tmp_path, monkeypatch) -> None:
    """Отчёт не должен делать вид, что эффекты применены к вокалу в миксе."""
    scaffold = _wav(tmp_path / "scaffold.wav")
    _patch_synth(monkeypatch, {
        "ok": True, "path": scaffold, "synthetic": True, "blocked": True,
    })
    _patch_rvc(monkeypatch, {"ok": True, "blocked": True, "path": "", "reason": "P0.05"})

    stages, _final, _warnings = vocal_chain._run_vocal_chain(
        _recipe(), "строка", tmp_path
    )

    fx = _by_name(stages)["_stage_vocal_fx"]
    assert fx.output in (None, {}), "у заблокированной стадии не должно быть ok=True"
    assert "synthetic" in fx.reason


# --------------------------------------------------------------------------- #
#  Настоящий вокал обрабатывается как раньше
# --------------------------------------------------------------------------- #

def test_real_recording_still_gets_vocal_fx(tmp_path, monkeypatch) -> None:
    vocal = _wav(tmp_path / "vocal.wav")
    fx_out = _wav(tmp_path / "fx.wav")
    _patch_synth(monkeypatch, {
        "ok": True, "path": vocal, "engine": "user_recording",
    })
    _patch_rvc(monkeypatch, {"ok": True, "blocked": True, "path": "", "reason": "no model"})
    calls: list = []

    def fake_fx(path, *_a, **_k):
        calls.append(path)
        return {"ok": True, "path": fx_out, "engine": "numpy_vocal_fx"}

    monkeypatch.setattr(vocal_chain, "_stage_vocal_fx", fake_fx)

    stages, vocal_final, _warnings = vocal_chain._run_vocal_chain(
        _recipe(), "строка", tmp_path
    )

    assert calls == [vocal]
    assert vocal_final == fx_out
    assert _by_name(stages)["_stage_vocal_fx"].ok is True


def test_synthetic_scaffold_with_working_rvc_still_gets_fx(tmp_path, monkeypatch) -> None:
    """Если RVC всё-таки дал реальный голос, каркас уже не каркас — эффекты нужны."""
    scaffold = _wav(tmp_path / "scaffold.wav")
    converted = _wav(tmp_path / "converted.wav")
    _patch_synth(monkeypatch, {"ok": True, "path": scaffold, "synthetic": True, "blocked": True})
    _patch_rvc(monkeypatch, {"ok": True, "path": converted, "engine": "rvc_python"})
    calls: list = []

    def fake_fx(path, *_a, **_k):
        calls.append(path)
        return {"ok": True, "path": path}

    monkeypatch.setattr(vocal_chain, "_stage_vocal_fx", fake_fx)

    stages, vocal_final, warnings = vocal_chain._run_vocal_chain(
        _recipe(), "строка", tmp_path
    )

    assert calls == [converted]
    assert vocal_final == converted
    assert not any("synthetic scaffold not mixed" in warning for warning in warnings)
    assert _by_name(stages)["_stage_vocal_fx"].ok is True


def test_fx_failure_on_real_vocal_is_not_hidden(tmp_path, monkeypatch) -> None:
    vocal = _wav(tmp_path / "vocal.wav")
    _patch_synth(monkeypatch, {"ok": True, "path": vocal, "engine": "user_recording"})
    _patch_rvc(monkeypatch, {"ok": True, "blocked": True, "path": ""})
    monkeypatch.setattr(
        vocal_chain, "_stage_vocal_fx",
        lambda *_a, **_k: {"ok": False, "reason": "no pedalboard", "fallback_used": True},
    )

    _stages, vocal_final, _warnings = vocal_chain._run_vocal_chain(
        _recipe(), "строка", tmp_path
    )

    # отказ эффектов не отнимает у микса исходный вокал
    assert vocal_final == vocal

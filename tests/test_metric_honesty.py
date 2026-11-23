"""Балл на оценке должен быть виден как оценка, а не как измерение.

Найдено в 42.0.19. Когда `pyloudnorm` падал (или отсутствовал),
`modules/hit_scorer` подменял LUFS на RMS-оценку и **продолжал считать балл**.
В отчёте при этом не было ни одного предупреждения, а подсказка к метрике
по-прежнему утверждала «integrated dBFS ≈ LUFS» — то есть человек читал
«громкость 75 из 100» как измеренный факт.

Честное поведение: провенанс метрики (`engine: rms_estimate`) обязан
порождать предупреждение в отчёте и менять подсказку на «это оценка».
"""

from __future__ import annotations

import numpy as np
import pytest

from modules.dsp.wavio import write_wav
from modules.hit_scorer import scoring
import modules.hit_scorer.mix_metrics as mix_metrics


@pytest.fixture()
def tone_file(tmp_path):
    sr = 22050
    t = np.arange(sr * 3)
    y = (0.2 * np.sin(t * 0.05)).astype("float32")
    path = tmp_path / "tone.wav"
    write_wav(path, np.stack([y, y], axis=1), sr, subtype="FLOAT")
    return str(path)


def _break_pyloudnorm(monkeypatch):
    """Смоделировать сбой измерителя: пакет есть, но падает."""

    class _BadMeter:
        def __init__(self, sr):  # noqa: ARG002 - API pyloudnorm
            pass

        def integrated_loudness(self, y):  # noqa: ARG002
            raise RuntimeError("meter broke")

    class _FakePyln:
        Meter = _BadMeter

    monkeypatch.setattr(mix_metrics, "HAS_PYLOUDNORM", True)
    monkeypatch.setattr(mix_metrics, "pyln", _FakePyln, raising=False)


def test_failed_loudness_meter_produces_a_warning(tone_file, monkeypatch):
    _break_pyloudnorm(monkeypatch)
    report = scoring.score_track(tone_file)
    warnings = report.get("warnings") or []
    assert any("loudness not measured" in w for w in warnings), warnings


def test_failed_loudness_meter_changes_the_hint(tone_file, monkeypatch):
    """Подсказка не может утверждать «это LUFS», если это RMS-оценка."""
    _break_pyloudnorm(monkeypatch)
    report = scoring.score_track(tone_file)
    metric = report["metrics"]["loudness_lufs"]
    assert metric["provenance"]["engine"] == "rms_estimate"
    assert "оценка" in metric["hint"].lower()


def test_measured_loudness_has_no_warning(tone_file):
    """Здоровый измеритель не должен порождать шум в отчёте."""
    report = scoring.score_track(tone_file)
    provenance = report["metrics"]["loudness_lufs"]["provenance"]
    if provenance.get("engine") == "pyloudnorm":
        assert not report.get("warnings")
    else:  # окружение без pyloudnorm — тогда предупреждение обязано быть
        assert report.get("warnings")


def test_hit_score_stage_forwards_scorer_warnings(monkeypatch):
    """`_stage_hit_score` не должен съедать предупреждения оценщика."""
    from app.core.stages import master as master_stage

    monkeypatch.setattr(
        "modules.hit_scorer.score_track",
        lambda path: {
            "hit_score": 70.0,
            "verdict": "solid",
            "metrics": {},
            "warnings": ["loudness not measured (rms_estimate)"],
        },
    )
    result = master_stage._stage_hit_score("/tmp/does-not-matter.wav")
    assert result["warnings"] == ["loudness not measured (rms_estimate)"]


def test_report_finalize_lifts_stage_warnings():
    """Предупреждения стадий обязаны попадать в итоговый список отчёта."""
    from app.core.report_finalize import _stage_warnings

    class _Stage:
        def __init__(self, output):
            self.output = output

    stages = [
        _Stage({"warnings": ["loudness not measured (rms_estimate)"]}),
        _Stage({}),
        _Stage({"warnings": ["dup", "dup"]}),
    ]
    collected = _stage_warnings(stages)
    assert collected == ["loudness not measured (rms_estimate)", "dup"]

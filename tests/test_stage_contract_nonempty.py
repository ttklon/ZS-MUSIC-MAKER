"""Контракт стадий: стадия не может быть `OK` с пустым выходом.

Гейт из T1 (`docs/IMPROVEMENT_PLAN.md`). Раньше `_stage_arrangement` возвращала
`{"ok": True, "plan": {"sections": []}}` — статус `OK`, отчёт зелёный, а стадия
не делала ничего. Такой «успех» запрещён контрактом: у стадии, объявленной как
содержательная, должен быть непустой ключевой результат.
"""

from __future__ import annotations

import pytest

from app.core.pipeline_runtime import STAGE_CONTRACT, _quality_gate_failures
from app.pipeline import classify


def test_contract_covers_every_meaningful_stage() -> None:
    """Каждая контрактная стадия обязана иметь объявленные непустые ключи."""
    assert STAGE_CONTRACT, "контракт стадий не должен быть пустым"
    for name, keys in STAGE_CONTRACT.items():
        assert name.startswith("_stage_"), name
        assert keys, f"у стадии {name} не объявлен ни один ключ результата"


def _stage(name: str, output: dict):
    return classify(output, name=name)


def test_empty_arrangement_plan_fails_the_contract() -> None:
    """Ровно тот баг из отчёта: ok=True, но план пуст."""
    stages = [
        _stage("_stage_arrangement", {"ok": True, "plan": {"sections": []}}),
        _stage("_stage_beat", {"ok": True, "path": "beat.wav"}),
    ]

    failures = _quality_gate_failures(stages)

    assert any("_stage_arrangement" in failure for failure in failures), failures


def test_missing_key_is_reported_as_contract_violation() -> None:
    stages = [_stage("_stage_beat", {"ok": True})]

    failures = _quality_gate_failures(stages)

    assert any("_stage_beat" in failure for failure in failures), failures


def test_beat_with_path_passes_contract() -> None:
    stages = [_stage("_stage_beat", {"ok": True, "path": "beat.wav"})]

    assert _quality_gate_failures(stages) == []


@pytest.mark.parametrize(
    "name, output",
    [
        ("_stage_mastering", {"ok": True, "masters": {"streaming": "master_streaming.wav"}}),
        ("_stage_release_pack", {"ok": True, "release_dir": "/tmp/release", "files": {"a": "b"}}),
        ("_stage_mix_and_sidechain", {"ok": True, "out_wav": "mix.wav"}),
        ("_stage_lyrics", {"ok": True, "text": "строка"}),
    ],
)
def test_non_empty_outputs_pass_contract(name: str, output: dict) -> None:
    assert _quality_gate_failures([_stage(name, output)]) == []


def test_blocked_stage_is_exempt() -> None:
    """Честный BLOCKED не обязан иметь результат — иначе он станет «провалом»."""
    stages = [_stage("_stage_beat", {"ok": True, "blocked": True, "reason": "skipped"})]

    assert _quality_gate_failures(stages) == []


def test_synthetic_fallback_is_exempt() -> None:
    """Fallback уже помечен и понижает вердикт отдельно, контракт его не дублирует."""
    stages = [
        _stage("_stage_lyrics", {"ok": True, "fallback_used": True, "text": "x"}),
    ]

    assert _quality_gate_failures(stages) == []


def test_dry_run_records_are_not_penalised() -> None:
    """В dry-run значения-заглушки ожидаемы: ``dry_run`` уже отдельный статус."""
    stages = [
        _stage("_stage_beat", {"ok": True, "blocked": True, "dry_run": True, "reason": "skipped"}),
        _stage("_stage_arrangement", {"ok": True, "dry_run": True, "plan": {}}),
    ]

    assert _quality_gate_failures(stages) == []

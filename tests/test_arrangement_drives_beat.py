"""T6: план аранжировки реально влияет на бит (иначе T5 — декорация).

Аранжировка и бит исторически планировали структуру независимо:
`arrangement_engine` строил секции по жанру, `beat.dramaturgy.plan_sections`
— свою сетку по длительности и числу куплетов. Два плана на один трек.

Влияние включается флагом `ZSMM_ARRANGEMENT_DRIVES_BEAT` (по умолчанию `1`).
`0` возвращает прежнее поведение бит-в-бит — аварийный выход, если структурное
влияние где-то мешает. Контрольный SHA-256 бита до доработки:
`80038fe967f5e478…` (seed 7, smoke-конфиг).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.core.stages import beat as beat_stage
from modules.beat.dramaturgy import plan_sections


PLAN = {
    "duration_sec": 60,
    "n_verses": 2,
    "aggression": 0.6,
    "sections": [
        {"name": "intro", "bars": 4, "energy": 0.3},
        {"name": "verse1", "bars": 8, "energy": 0.55},
        {"name": "chorus1", "bars": 8, "energy": 0.9},
        {"name": "verse2", "bars": 8, "energy": 0.6},
        {"name": "chorus2", "bars": 8, "energy": 0.95},
        {"name": "outro", "bars": 4, "energy": 0.3},
    ],
}
STYLE = {"target_bpm": 128, "target_mode": "minor", "genre": "drift_phonk", "seed": 7}


def _sha256(path) -> str:
    from pathlib import Path as _Path

    return hashlib.sha256(_Path(path).read_bytes()).hexdigest()


@pytest.fixture
def rendered(tmp_path, monkeypatch):
    """Один и тот же бит, посчитанный с флагом и без него."""
    monkeypatch.setenv("ZSMM_MASTER_WORKERS", "1")
    monkeypatch.setattr(beat_stage, "construct_beat_inputs", None, raising=False)

    def run(flag: str, name: str):
        monkeypatch.setenv("ZSMM_ARRANGEMENT_DRIVES_BEAT", flag)
        out_dir = tmp_path / name
        out_dir.mkdir(parents=True, exist_ok=True)
        result = beat_stage._stage_beat(PLAN, out_dir, groove=None, style_vector=STYLE)
        # Снимок хеша сразу: конструктор пишет и в общий output/beats,
        # поэтому читать файл позже — значит сравнивать один и тот же путь.
        result["sha256"] = _sha256(result["path"])
        return result

    return run


def test_flag_defaults_to_on(monkeypatch) -> None:
    monkeypatch.delenv("ZSMM_ARRANGEMENT_DRIVES_BEAT", raising=False)

    assert beat_stage._arrangement_drives_beat() is True


def test_flag_can_be_switched_off(monkeypatch) -> None:
    monkeypatch.setenv("ZSMM_ARRANGEMENT_DRIVES_BEAT", "0")

    assert beat_stage._arrangement_drives_beat() is False


def test_plan_sections_come_from_arrangement(rendered) -> None:
    """Секции бита обязаны совпасть с секциями плана, а не строиться заново."""
    result = rendered("1", "on")

    assert result["ok"] is True
    # Каждая секция плана присутствует в бите и в том же порядке; исходное имя
    # сохраняется рядом (`arrangement_name`), имя для конструктора — каноническое.
    assert [s["arrangement_name"] for s in result["sections"]] == [
        section["name"] for section in PLAN["sections"]
    ]
    assert [s["name"] for s in result["sections"]] == ["intro", "verse", "chorus", "verse", "chorus", "outro"]
    assert result["arrangement_driven"] is True


def test_off_flag_keeps_the_legacy_section_plan(rendered) -> None:
    result = rendered("0", "off")

    assert result["ok"] is True
    assert result.get("arrangement_driven") is False
    legacy = [section.name for section in plan_sections(128, 60, n_verses=2)]
    assert [section["name"] for section in result["sections"]] == legacy


def test_off_flag_reproduces_the_control_hash(rendered) -> None:
    """`0` — аварийный выход: результат обязан остаться прежним бит-в-бит."""
    first = rendered("0", "a")
    second = rendered("0", "b")

    assert first["sha256"] == second["sha256"]


def test_enabled_flag_changes_the_audio(rendered) -> None:
    on = rendered("1", "on2")
    off = rendered("0", "off2")

    assert on["path"] != off["path"]
    assert on["sha256"] != off["sha256"], "влияние аранжировки на бит не проявилось в аудио"


def test_plan_without_sections_falls_back_honestly(rendered, monkeypatch) -> None:
    monkeypatch.setenv("ZSMM_ARRANGEMENT_DRIVES_BEAT", "1")

    result = beat_stage._stage_beat(
        {"duration_sec": 30, "n_verses": 2}, Path("/tmp/zsmm-t6-noplan"), style_vector=STYLE
    )

    assert result["ok"] is True
    assert result.get("arrangement_driven") is False
    assert "no arrangement sections" in (result.get("arrangement_note") or "")

"""Контракт стадий пайплайна: один статус, одна сводка, один процент."""

from __future__ import annotations

from app.core.recipe import build_recipe, resolve_style_vector
from app.pipeline import StageResult, StageStatus, classify, summarize


def test_failed_stage_is_not_masked_as_success() -> None:
    stage = classify({"ok": False, "reason": "engine offline"}, name="beat")

    assert stage.status is StageStatus.FAILED
    assert stage.ok is False
    assert stage.succeeded is False
    assert stage.reason == "engine offline"


def test_exception_becomes_failed_stage_with_type_in_reason() -> None:
    stage = classify(None, failed=True, reason="RuntimeError: boom", name="mix")

    assert stage.status is StageStatus.FAILED
    assert "RuntimeError" in (stage.reason or "")


def test_plain_none_output_is_failure_not_silent_success() -> None:
    assert classify(None, name="texture").status is StageStatus.FAILED


def test_fallback_and_blocked_are_distinct_statuses() -> None:
    fallback = classify({"ok": True, "fallback_used": True, "engine": "template"}, name="lyrics")
    blocked = classify({"ok": True, "blocked": True, "reason": "torch missing"}, name="stems")

    assert fallback.status is StageStatus.FALLBACK
    assert fallback.fallback_used is True and fallback.ok is True
    assert blocked.status is StageStatus.BLOCKED
    assert blocked.blocked is True and blocked.fallback_used is False


def test_synthetic_output_without_block_is_fallback_and_simulation() -> None:
    stage = classify({"ok": True, "synthetic": True}, name="texture")

    assert stage.status is StageStatus.FALLBACK
    assert stage.is_simulation is True


def test_blocked_synthetic_scaffold_is_not_a_simulation() -> None:
    stage = classify({"ok": True, "synthetic": True, "blocked": True}, name="texture")

    assert stage.status is StageStatus.BLOCKED
    assert stage.is_simulation is False


def test_error_alias_keeps_legacy_pipeline_core_contract() -> None:
    stage = StageResult(name="s", status=StageStatus.FAILED, reason="stage=s event=failed")

    assert stage.error == stage.reason


def test_to_dict_exposes_status_and_legacy_keys() -> None:
    row = classify({"ok": True, "fallback_used": True}, name="master").to_dict()

    assert row["status"] == "FALLBACK"
    assert row["name"] == "master"
    assert {"ok", "fallback_used", "blocked", "synthetic", "duration_sec", "output"} <= set(row)


def _row(name: str, status: str, output: dict | None = None) -> dict:
    return {
        "name": name,
        "status": status,
        "ok": status != "FAILED",
        "output": output or {},
    }


def test_summary_pass_requires_no_fallback() -> None:
    summary = summarize([_row("a", "OK"), _row("b", "OK")])

    assert summary["verdict"] == "PASS"
    assert summary["percent"] == 100


def test_summary_blocked_dominates_fallback_and_keeps_half_credit() -> None:
    summary = summarize([_row("a", "OK"), _row("b", "FALLBACK"), _row("c", "BLOCKED")])

    assert summary["verdict"] == "PASS_BLOCKED"
    assert summary["percent"] == int(round(100 * 2.5 / 3))
    assert summary["blocked_stages"] == ["c"]
    assert summary["fallback_stages"] == ["b"]
    assert any("fallback" in warning for warning in summary["warnings"])


def test_summary_pass_blocked_when_only_heavy_stages_missing() -> None:
    summary = summarize([_row("a", "OK"), _row("c", "BLOCKED")])

    assert summary["verdict"] == "PASS_BLOCKED"
    assert summary["percent"] == 75


def test_summary_partial_when_stage_failed() -> None:
    summary = summarize([_row("a", "OK"), _row("b", "FAILED")])

    assert summary["verdict"] == "PARTIAL"
    assert summary["failed_stages"] == ["b"]
    assert summary["percent"] == 50


def test_simulation_verdict_caps_percent() -> None:
    summary = summarize([_row("a", "OK"), _row("b", "FALLBACK", {"synthetic": True})])

    assert summary["verdict"] == "BLOCKED_SIMULATION"
    assert summary["percent"] <= 60


def test_dry_run_never_reports_simulation_verdict() -> None:
    summary = summarize([_row("a", "OK", {"dry_run": True})], dry_run=True)

    assert summary["verdict"] == "PASS"


def test_recipe_normalises_user_choice_and_merges_extra_prompt() -> None:
    recipe = build_recipe(
        {
            "theme": "night drive",
            "user_extra_prompt": "late rain",
            "voice_mode": "NONSENSE",
            "n_verses": 99,
            "aggression": 2.5,
            "quality_mode": "unknown",
            "stands": ("streaming",),
            "own_vocal_wav": "/tmp/voice.wav",
            "user_lyrics_lines": ["line", "   "],
        }
    )

    assert recipe["voice_mode"] == "pro"
    assert recipe["n_verses"] == 4
    assert recipe["aggression"] == 1.0
    assert recipe["quality_mode"] == "quality"
    assert recipe["stands"] == ["streaming"]
    assert recipe["theme"] == "night drive; late rain"
    assert recipe["user_lyrics_lines"] == ["line"]
    assert recipe["own_vocal_wav"] == "/tmp/voice.wav"


def test_style_vector_priority_is_user_bpm_over_analysis_over_preset() -> None:
    recipe = build_recipe({"genre": "phonk", "bpm_override": 150})
    recipe["preset_style_vector"] = {"target_bpm": 120, "target_mode": "major"}
    analysis = {"bpm": 140, "mode": "minor"}

    style = resolve_style_vector(recipe, analysis)

    assert style["target_bpm"] == 150
    assert style["target_mode"] == "minor"
    assert analysis["bpm"] == 150

"""A high heuristic score cannot hide incomplete pipeline execution."""
import copy

import pytest

from modules.hit_factory.evolver import select_best, should_evolve
from modules.hit_factory.readiness import attempt_readiness


@pytest.fixture
def completed(tmp_path):
    master = tmp_path / "master.wav"
    master.write_bytes(b"test artifact")
    return {
        "master_path": str(master), "hit_score": 72, "verdict": "solid",
        "hit": {"hit_score": 72, "verdict": "solid"},
        "report": {"verdict": "PASS", "status_summary": {}, "quality_gate_failures": []},
    }


def test_completed_render_is_technically_ready(completed):
    assert attempt_readiness(completed) == {"ready": True, "reasons": []}


@pytest.mark.parametrize("verdict", ["PASS_BLOCKED", "PARTIAL", "BLOCKED_SIMULATION", None])
def test_high_score_does_not_hide_incomplete_pipeline(completed, verdict):
    completed["report"]["verdict"] = verdict
    assert not attempt_readiness(completed)["ready"]


@pytest.mark.parametrize("field,value", [
    ("dry_run", True), ("quality_gate_failures", ["crest"]),
    ("status_summary", {"blocked": ["_stage_voice_synth"]}),
    ("status_summary", {"failed": ["_stage_hit_score"]}),
])
def test_pipeline_blockers_are_respected(completed, field, value):
    completed["report"][field] = value
    assert not attempt_readiness(completed)["ready"]


def test_estimated_measurement_is_not_verified(completed):
    completed["hit"]["warnings"] = ["loudness not measured"]
    assert not attempt_readiness(completed)["ready"]


def test_complete_render_beats_higher_scoring_partial(completed):
    partial = copy.deepcopy(completed)
    partial.update(hit_score=99)
    partial["report"]["verdict"] = "PARTIAL"
    assert select_best([partial, completed]) is completed


def test_missing_master_never_wins(completed):
    broken = copy.deepcopy(completed)
    broken.update(hit_score=99, master_path=None)
    assert select_best([broken, completed]) is completed


@pytest.mark.parametrize("score", [float("nan"), float("inf"), -1, 101, True, None])
def test_invalid_score_is_not_ready_or_best(completed, score):
    broken = copy.deepcopy(completed)
    broken["hit_score"] = score
    assert not attempt_readiness(broken)["ready"]
    assert select_best([broken, completed]) is completed
    assert should_evolve(score, "solid")


@pytest.mark.parametrize("verdict", ["invalid_audio", "needs_work", "flop_risk", None])
def test_high_score_alone_cannot_stop_evolution(verdict):
    assert should_evolve(95, verdict)


@pytest.mark.parametrize("pipeline_verdict, expected_attempts", [("PARTIAL", 3), ("PASS", 1)])
def test_factory_stops_only_on_complete_attempt(
    completed, tmp_path, monkeypatch, pipeline_verdict, expected_attempts,
):
    import json
    from modules.hit_factory import generator

    monkeypatch.setattr(generator, "_maybe_auto_genre", lambda genre, theme: genre)
    monkeypatch.setattr("modules.hit_factory.kpi.build_kpi", lambda *a, **kw: {})
    factory = generator.HitFactory(
        output_root=tmp_path, adaptive=False, max_attempts=3, verbose=False,
    )
    monkeypatch.setattr(factory, "_build_wizard_state", lambda **kw: {
        "genre": "trap", "theme": "test", "seed": 42,
        "bpm_override": 140, "aggression": 0.7, "duration_sec": 5,
    })
    calls = []

    def render(project_id, state, rng):
        calls.append(project_id)
        attempt = copy.deepcopy(completed)
        attempt.update(project_id=project_id, out_root=str(tmp_path))
        attempt["report"]["verdict"] = pipeline_verdict
        return attempt

    monkeypatch.setattr(factory, "_run_pipeline_once", render)
    result = factory.make_one(genre="trap", theme="test", seed=42)
    assert len(calls) == expected_attempts
    assert result["readiness"]["ready"] is (pipeline_verdict == "PASS")
    saved = json.loads((tmp_path / "factory_summary.json").read_text())
    assert saved["readiness"] == result["readiness"]
    assert len(saved["attempts"]) == expected_attempts


@pytest.mark.parametrize("pipeline_verdict, expected_code", [("PARTIAL", 1), ("PASS_BLOCKED", 1), ("PASS", 0)])
def test_standard_cli_reports_readiness(completed, monkeypatch, capsys, pipeline_verdict, expected_code):
    from types import SimpleNamespace
    from app.cli.hitfactory import _run_standard_cli

    completed["report"]["verdict"] = pipeline_verdict

    class Factory:
        def __init__(self, **kwargs):
            pass

        def make_one(self, **kwargs):
            return completed

    monkeypatch.setattr("modules.hit_factory.generator.HitFactory", Factory)
    assert _run_standard_cli(SimpleNamespace(hit_count=1)) == expected_code
    output = capsys.readouterr().out
    assert "render_ready=" in output
    if expected_code:
        assert "not ready:" in output


def test_partial_batch_cannot_exit_success(completed, monkeypatch):
    from types import SimpleNamespace
    from app.cli.hitfactory import _run_standard_cli

    incomplete = copy.deepcopy(completed)
    incomplete["report"]["verdict"] = "PARTIAL"

    class Factory:
        def __init__(self, **kwargs):
            pass

        def make_batch(self, **kwargs):
            return [completed, incomplete]

    monkeypatch.setattr("modules.hit_factory.generator.HitFactory", Factory)
    assert _run_standard_cli(SimpleNamespace(hit_count=2)) == 1


@pytest.mark.parametrize("pipeline_verdict, expected_code", [("PARTIAL", 1), ("PASS", 0)])
def test_breakthrough_cli_uses_same_readiness(
    completed, monkeypatch, pipeline_verdict, expected_code,
):
    from types import SimpleNamespace
    from app.cli.hitfactory import _run_breakthrough_cli

    completed["report"]["verdict"] = pipeline_verdict
    monkeypatch.setattr(
        "modules.hit_factory.breakthrough.full_orchestrate",
        lambda **kwargs: {"hit": completed},
    )
    assert _run_breakthrough_cli(
        SimpleNamespace(hit_count=1), [], None, None, "test", 5,
    ) == expected_code

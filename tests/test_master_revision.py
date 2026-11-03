"""Verified mix reuse; mocked stages test orchestration, not AI inference."""
from pathlib import Path
import json

import numpy as np
import pytest
import soundfile as sf

from app.core import orchestrator
from app.core.revision import prepare_master_revision
from app.pipeline import StageResult, StageStatus
from app.runtime_orchestrator import Job, RuntimeOrchestrator


def _tone(path: Path, value: float = .1) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, value * np.sin(np.arange(8000) * .1), 8000)
    return str(path)


@pytest.fixture
def source_project(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(orchestrator, "_stage_analyze", lambda *a, **k: calls.append("analyze") or {"ok": True, "analysis": {"bpm": 100}})
    monkeypatch.setattr(orchestrator, "_stage_groove", lambda *a, **k: {"ok": True, "groove": {}})
    monkeypatch.setattr(orchestrator, "_stage_arrangement", lambda *a, **k: {"ok": True, "plan": {}})
    monkeypatch.setattr(orchestrator, "_stage_beat", lambda plan, out, **kw: {"ok": True, "path": _tone(out / "beat.wav"), "bpm": 100, "key": "A minor"})
    monkeypatch.setattr(orchestrator, "_stage_texture", lambda *a: {"ok": True, "blocked": True, "reason": "no AI texture"})
    monkeypatch.setattr(orchestrator, "_run_lyrics_stage", lambda recipe: (
        StageResult(name="_stage_lyrics", status=StageStatus.FALLBACK, output={
            "ok": True, "text": "слова", "lyrics": {"title": "Тест"}, "fallback_used": True}),
        {"title": "Тест"}, "слова"))
    monkeypatch.setattr(orchestrator, "_run_vocal_chain", lambda *a, **k: ([
        StageResult(name="_stage_voice_synth", status=StageStatus.OK, output={"ok": True}),
        StageResult(name="_stage_rvc", status=StageStatus.BLOCKED, reason="RVC disabled"),
        StageResult(name="_stage_vocal_fx", status=StageStatus.OK, output={"ok": True})], "voice.wav", []))
    monkeypatch.setattr(orchestrator, "_stage_mix_and_sidechain", lambda beat, voice, out, *a, **kw: {
        "ok": True, "out_wav": _tone(out / "mix.wav"), "vocal_used": True,
        "gates_passed": False, "gates": {"correlation": False}})
    def master(mix, out, stands=None):
        calls.append(("master", mix, stands))
        return {"ok": True, "masters": {"streaming": _tone(out / "masters/streaming.wav")},
                "summary": {"gates_passed": True}}
    monkeypatch.setattr(orchestrator, "_stage_mastering", master)
    monkeypatch.setattr(orchestrator, "_stage_polish", lambda path, out: {"ok": True, "path": path})
    monkeypatch.setattr(orchestrator, "_stage_hit_score", lambda path: {"ok": True, "hit_score": 10})
    def release(master_path, metadata, *a, **kw):
        calls.append(("release", metadata))
        return {"ok": True, "path": "release"}
    monkeypatch.setattr(orchestrator, "_stage_release_pack", release)
    source = tmp_path / "source"
    recipe = {"genre": "house", "theme": "чай", "export_stems": False, "stands": ["streaming"]}
    report = orchestrator.run_full_pipeline("source-id", recipe, out_root=source)
    return source, recipe, report, calls


def test_master_revision_preserves_source_status_and_quality_failure(source_project, monkeypatch, tmp_path):
    source, recipe, report, calls = source_project
    original = (source / "mix.wav").read_bytes()
    source_report = (source / "report.json").read_bytes()
    assert report["artifact_integrity"]["mix"]["relative_path"] == "mix.wav"
    assert report["verdict"] == "PARTIAL"
    new_dir = tmp_path / "revision"
    reused = prepare_master_revision(source, new_dir, report)
    def forbidden(*args, **kwargs): pytest.fail("upstream stage must not run")
    for name in ("_stage_analyze", "_stage_groove", "_stage_arrangement", "_stage_beat", "_stage_texture", "_run_lyrics_stage", "_run_vocal_chain", "_stage_mix_and_sidechain"):
        monkeypatch.setattr(orchestrator, name, forbidden)
    events = []
    result = orchestrator.run_full_pipeline("revision-id", {**recipe, "stands": ["car"]},
                                            out_root=new_dir, reused_stages=reused,
                                            on_stage=lambda *a: events.append(a))
    stages = {stage["name"]: stage for stage in result["stages"]}
    assert len(events) == len(orchestrator.STAGE_RECORDS)
    assert all("(reused)" in event[1] for event in events[:10])
    assert all("(reused)" not in event[1] for event in events[10:])
    assert stages["_stage_lyrics"]["status"] == "FALLBACK"
    assert stages["_stage_rvc"]["status"] == "BLOCKED"
    assert stages["_stage_mix_and_sidechain"]["output"]["reused"] is True
    assert "mix: correlation" in result["quality_gate_failures"]
    assert result["verdict"] == "PARTIAL"
    assert result["revision"] == {"kind": "master", "source_project": "source-id"}
    assert (new_dir / "reused_mix.wav").read_bytes() == original
    assert (source / "mix.wav").read_bytes() == original
    assert (source / "report.json").read_bytes() == source_report
    master_call = [call for call in calls if call[0] == "master"][-1]
    assert master_call[2] == ["car"]
    release_call = [call for call in calls if call[0] == "release"][-1]
    assert release_call[1].get("beat_path") is None and release_call[1].get("vocal_path") is None
    assert result["artifact_integrity"]["mix"]["relative_path"] == "reused_mix.wav"


def test_changed_or_missing_mix_fails_without_using_old_audio(source_project, tmp_path):
    source, _, report, _ = source_project
    damaged = bytearray((source / "mix.wav").read_bytes())
    damaged[-1] ^= 1
    (source / "mix.wav").write_bytes(damaged)
    with pytest.raises(ValueError, match="integrity check"):
        prepare_master_revision(source, tmp_path / "new", report)
    assert not (tmp_path / "new" / "reused_mix.wav").exists()
    report["artifact_integrity"]["mix"]["relative_path"] = "../outside.wav"
    with pytest.raises(ValueError, match="invalid mix path"):
        prepare_master_revision(source, tmp_path / "new", report)
    report.pop("artifact_integrity")
    with pytest.raises(ValueError, match="no mix integrity"):
        prepare_master_revision(source, tmp_path / "new", report)


def test_runtime_revision_uses_source_recipe_and_only_allowed_overrides(source_project, monkeypatch, tmp_path):
    source, recipe, report, _ = source_project
    import app.runtime_orchestrator as runtime_module
    monkeypatch.setattr(runtime_module, "ROOT", tmp_path)
    runtime = RuntimeOrchestrator()
    runtime.stop()
    monkeypatch.setattr(runtime, "_ensure_worker", lambda: None)
    runtime.jobs["source-id"] = Job(track_id="source-id", recipe=recipe, status="done", project_dir=str(source), result={"pipeline": report})
    tid = runtime.enqueue_master_revision("source-id", {"stands": ["car"], "theme": "must not change", "export_stems": False})
    job = runtime.jobs[tid]
    assert job.recipe["theme"] == "чай" and job.recipe["stands"] == ["car"]
    runtime._process(job)
    assert job.status == "done", job.error
    assert job.result["pipeline"]["revision"]["source_project"] == "source-id"
    assert json.loads((Path(job.project_dir) / "report.json").read_text(encoding="utf-8"))["verdict"] == "PARTIAL"


def test_source_with_partial_or_duplicate_report_is_rejected(source_project, tmp_path):
    source, _, report, _ = source_project
    report["only"] = ["mix"]
    with pytest.raises(ValueError, match="full non-resumed"):
        prepare_master_revision(source, tmp_path / "new", report)
    report["only"] = None
    report["stages"].append(report["stages"][0])
    with pytest.raises(ValueError, match="duplicate"):
        prepare_master_revision(source, tmp_path / "new", report)


def test_rejects_symlink_outside_and_mismatched_stage_path(source_project, tmp_path):
    source, _, report, _ = source_project
    original = source / "mix.wav"
    external = tmp_path / "external.wav"
    external.write_bytes(original.read_bytes())
    original.unlink()
    try:
        original.symlink_to(external)
    except OSError:
        pytest.skip("symlink creation unavailable")
    with pytest.raises(ValueError, match="symlink"):
        prepare_master_revision(source, tmp_path / "new", report)
    original.unlink()
    original.write_bytes(external.read_bytes())
    row = next(s for s in report["stages"] if s["name"] == "_stage_mix_and_sidechain")
    row["output"]["out_wav"] = str(external)
    with pytest.raises(ValueError, match="does not match"):
        prepare_master_revision(source, tmp_path / "new", report)


def test_rejects_same_project_and_invalid_source_status(source_project, tmp_path):
    source, _, report, _ = source_project
    with pytest.raises(ValueError, match="separate"):
        prepare_master_revision(source, source, report)
    with pytest.raises(ValueError, match="separate"):
        prepare_master_revision(source, source / "child", report)
    report["stages"][0]["status"] = "BOGUS"
    with pytest.raises(ValueError, match="invalid source status"):
        prepare_master_revision(source, tmp_path / "new", report)
    assert not (tmp_path / "new" / "reused_mix.wav").exists()


def test_a_revision_can_be_revised_again(source_project, tmp_path):
    source, recipe, report, _ = source_project
    first = tmp_path / "rev1"
    first_report = orchestrator.run_full_pipeline("rev1", recipe, out_root=first,
        reused_stages=prepare_master_revision(source, first, report))
    second = tmp_path / "rev2"
    second_report = orchestrator.run_full_pipeline("rev2", recipe, out_root=second,
        reused_stages=prepare_master_revision(first, second, first_report))
    assert second_report["revision"]["source_project"] == "rev1"
    assert second_report["verdict"] == "PARTIAL"
    assert (second / "reused_mix.wav").read_bytes() == (source / "mix.wav").read_bytes()


def test_mix_changed_during_mastering_is_not_offered_for_revision(source_project, monkeypatch, tmp_path):
    _, recipe, _, _ = source_project
    def modify_mix(mix, out, stands=None):
        _tone(Path(mix), value=.2)
        return {"ok": True, "masters": {"streaming": _tone(out / "masters/streaming.wav")}}
    monkeypatch.setattr(orchestrator, "_stage_mastering", modify_mix)
    result = orchestrator.run_full_pipeline("changed", recipe, out_root=tmp_path / "changed")
    assert "artifact_integrity" not in result
    assert any("mix changed during render" in item for item in result["warnings"])


def test_full_pipeline_passes_all_references_to_mix(source_project, monkeypatch, tmp_path):
    _, recipe, _, _ = source_project
    seen = []
    def mix(beat, vocal, out, references, **kwargs):
        seen.append(references)
        return {"ok": True, "out_wav": _tone(out / "mix.wav"), "gates_passed": True, "gates": {}}
    monkeypatch.setattr(orchestrator, "_stage_mix_and_sidechain", mix)
    refs = ["ref1.wav", "ref2.wav", "ref3.wav"]
    orchestrator.run_full_pipeline("all-refs", {**recipe, "references": refs}, out_root=tmp_path / "all-refs")
    assert seen == [refs]

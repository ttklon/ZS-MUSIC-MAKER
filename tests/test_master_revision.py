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


def test_reopen_after_restart_and_move_preserves_recipe_and_source(source_project, monkeypatch, tmp_path):
    import shutil
    import app.runtime_orchestrator as runtime_module
    source, recipe, report, calls = source_project
    moved = tmp_path / "moved"
    shutil.move(source, moved)
    assert not source.exists()
    original = {p.name: p.read_bytes() for p in moved.iterdir() if p.is_file()}
    monkeypatch.setattr(runtime_module, "ROOT", tmp_path)
    runtime = RuntimeOrchestrator()
    runtime.stop()
    monkeypatch.setattr(runtime, "_ensure_worker", lambda: None)
    opened_id = runtime.open_project(moved)
    opened = runtime.jobs[opened_id]
    assert opened.master_only and opened.recipe == recipe
    assert opened.source_report_id == "source-id" and opened_id != "source-id"
    new_id = runtime.enqueue_master_revision(opened_id, {"stands": ["car"], "export_stems": False})
    job = runtime.jobs[new_id]
    assert job.master_only
    runtime._process(job)
    assert job.status == "done", job.error
    assert job.result["pipeline"]["revision"]["source_project"] == "source-id"
    assert calls[-1][1]["theme"] == "чай"
    assert job.result["pipeline"]["desktop_recipe_snapshot"]["recipe"]["theme"] == "чай"
    assert (Path(job.project_dir) / "reused_mix.wav").read_bytes() == (moved / "mix.wav").read_bytes()
    assert {p.name: p.read_bytes() for p in moved.iterdir() if p.is_file()} == original
    runtime.stop()


def test_open_rejects_legacy_corrupt_and_damaged_reports(source_project, tmp_path):
    source, _, report, _ = source_project
    runtime = RuntimeOrchestrator()
    runtime.stop()
    path = source / "report.json"
    report.pop("desktop_recipe_snapshot")
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="no supported complete recipe"):
        runtime.open_project(source)
    path.write_text('{"project_id":"a", "project_id":"b"}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        runtime.open_project(source)
    path.write_text('{"project_id": NaN}', encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON constant"):
        runtime.open_project(source)
    path.write_text("{broken", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid project report"):
        runtime.open_project(source)


def test_open_and_revision_reject_changed_mix_or_report(source_project, monkeypatch, tmp_path):
    import app.runtime_orchestrator as runtime_module
    source, _, _, _ = source_project
    monkeypatch.setattr(runtime_module, "ROOT", tmp_path)
    runtime = RuntimeOrchestrator()
    runtime.stop()
    monkeypatch.setattr(runtime, "_ensure_worker", lambda: None)
    opened_id = runtime.open_project(source)
    report_path = source / "report.json"
    original_report = report_path.read_bytes()
    report_path.write_bytes(original_report + b" ")
    tid = runtime.enqueue_master_revision(opened_id)
    runtime._process(runtime.jobs[tid])
    assert runtime.jobs[tid].status == "error" and "report changed" in runtime.jobs[tid].error
    report_path.write_bytes(original_report)
    mix = source / "mix.wav"
    mix.write_bytes(mix.read_bytes() + b"x")
    with pytest.raises(ValueError, match="integrity check"):
        runtime.open_project(source)
    tid = runtime.enqueue_master_revision(opened_id)
    runtime._process(runtime.jobs[tid])
    assert runtime.jobs[tid].status == "error" and "integrity check" in runtime.jobs[tid].error


def test_reserved_project_collision_never_overwrites_existing_directory(monkeypatch, tmp_path):
    import app.runtime_orchestrator as runtime_module
    from types import SimpleNamespace
    monkeypatch.setattr(runtime_module, "ROOT", tmp_path)
    existing = tmp_path / "output" / "desktop_runs" / "collision"
    existing.mkdir(parents=True)
    (existing / "keep").write_text("safe")
    ids = iter([SimpleNamespace(hex="collision"), SimpleNamespace(hex="new")])
    monkeypatch.setattr(runtime_module.uuid, "uuid4", lambda: next(ids))
    runtime = RuntimeOrchestrator()
    runtime.stop()
    monkeypatch.setattr(runtime, "_ensure_worker", lambda: None)
    tid = runtime.enqueue({"theme": "test"})
    assert tid == "new" and (existing / "keep").read_text() == "safe"
    assert Path(runtime.jobs[tid].project_dir).is_dir()


def test_snapshot_is_exact_and_excludes_unknown_secret_fields():
    from app.core.project_snapshot import snapshot_recipe
    data = {"theme": "привет", "references": ["one", "two"], "user_lyrics_lines": ["слова"]}
    assert snapshot_recipe(data)["recipe"] == data
    for bad in ({"secret": "do not persist"}, {"theme": float("nan")}, {"references": ("a", "b")}):
        with pytest.raises(ValueError):
            snapshot_recipe(bad)


def test_snapshot_failure_is_explicit_and_does_not_persist_unknown_fields(source_project, tmp_path):
    _, recipe, _, _ = source_project
    report = orchestrator.run_full_pipeline('unknown', {**recipe, 'secret': 'private-value'}, out_root=tmp_path/'unknown')
    assert 'desktop_recipe_snapshot' not in report
    assert any('recipe not saved' in warning for warning in report['warnings'])
    assert 'private-value' not in (tmp_path/'unknown'/'report.json').read_text(encoding='utf-8')


def test_report_symlinks_and_oversize_are_rejected(source_project, tmp_path):
    from app.core.project_snapshot import MAX_REPORT_BYTES, read_project_report
    source, _, _, _ = source_project
    link_dir = tmp_path/'links'
    link_dir.mkdir()
    try:
        (link_dir/'report.json').symlink_to(source/'report.json')
    except OSError:
        pytest.skip('symlink creation unavailable')
    with pytest.raises(ValueError, match='symlink'):
        read_project_report(link_dir)
    (link_dir/'report.json').unlink()
    (link_dir/'report.json').write_bytes(b' ' * (MAX_REPORT_BYTES + 1))
    with pytest.raises(ValueError, match='size limit'):
        read_project_report(link_dir)


def test_revision_rejects_failed_or_malformed_report(source_project, tmp_path):
    source, _, report, _ = source_project
    report['verdict'] = 'FAILED'
    with pytest.raises(ValueError, match='failed verdict'):
        prepare_master_revision(source, tmp_path/'new', report)
    report['verdict'] = 'PARTIAL'
    report['stages'][0]['attempts'] = 'invalid'
    with pytest.raises(ValueError, match='invalid source stage data'):
        prepare_master_revision(source, tmp_path/'new', report)
    assert not (tmp_path/'new').exists()


def test_reopened_revision_can_itself_be_reopened(source_project, monkeypatch, tmp_path):
    import app.runtime_orchestrator as runtime_module
    source, recipe, _, _ = source_project
    monkeypatch.setattr(runtime_module, 'ROOT', tmp_path)
    runtime = RuntimeOrchestrator()
    runtime.stop()
    monkeypatch.setattr(runtime, '_ensure_worker', lambda: None)
    opened = runtime.open_project(source)
    first = runtime.enqueue_master_revision(opened)
    runtime._process(runtime.jobs[first])
    assert runtime.jobs[first].status == 'done'
    other = RuntimeOrchestrator()
    other.stop()
    monkeypatch.setattr(other, '_ensure_worker', lambda: None)
    opened_again = other.open_project(runtime.jobs[first].project_dir)
    assert other.jobs[opened_again].recipe == recipe
    next_id = other.enqueue_master_revision(opened_again)
    other._process(other.jobs[next_id])
    assert other.jobs[next_id].status == 'done', other.jobs[next_id].error
    assert other.jobs[next_id].result['pipeline']['revision']['source_project'] == first


def test_full_rebuild_after_reopen_freezes_verified_inputs(source_project, monkeypatch, tmp_path):
    import app.runtime_orchestrator as runtime_module
    _, _, _, calls = source_project
    monkeypatch.setattr(runtime_module, 'ROOT', tmp_path)
    monkeypatch.setattr(orchestrator, '_stage_ai_beat', lambda recipe, plan, out, style, dry: {
        'ok': True, 'path': _tone(out / 'beat.wav'), 'bpm': 100})
    files = [tmp_path / name for name in ('ref-a.wav', 'ref-b.wav', 'backing.wav', 'voice.wav', 'model.pth', 'voice.index')]
    for index, file in enumerate(files):
        file.write_bytes(('input' + str(index)).encode())
    recipe = {'genre': 'house', 'theme': 'сохранённая тема', 'artist': 'автор',
              'references': [str(files[0]), str(files[1])], 'beat_engine': 'user_audio',
              'beat_input_path': str(files[2]), 'own_vocal_wav': str(files[3]),
              'voice_mode': 'pro', 'use_rvc': True, 'rvc_model_path': str(files[4]),
              'rvc_index_path': str(files[5]), 'reference_lyrics': 'личный текст',
              'user_lyrics_lines': ['строка'], 'trend_notes': 'заметка', 'export_stems': False}
    source = tmp_path / 'source-full'
    report = orchestrator.run_full_pipeline('full-source', recipe, out_root=source)
    assert len(report['input_integrity']['files']) == 6
    original_report = (source / 'report.json').read_bytes()
    original_mix = (source / 'mix.wav').read_bytes()
    runtime = RuntimeOrchestrator()
    runtime.stop()
    monkeypatch.setattr(runtime, '_ensure_worker', lambda: None)
    opened = runtime.open_project(source)
    tid = runtime.enqueue_opened_rebuild(opened)
    job = runtime.jobs[tid]
    runtime._process(job)
    assert job.status == 'done', job.error
    assert not job.master_only and job.recipe['theme'] == recipe['theme']
    assert job.recipe['reference_lyrics'] == 'личный текст'
    new_paths = [*job.recipe['references'], job.recipe['beat_input_path'], job.recipe['own_vocal_wav'],
                 job.recipe['rvc_model_path'], job.recipe['rvc_index_path']]
    for original, copied in zip(files, new_paths):
        assert Path(copied).is_relative_to(Path(job.project_dir) / 'input_files')
        assert Path(copied).read_bytes() == original.read_bytes()
    assert job.result['pipeline']['desktop_recipe_snapshot']['recipe'] == job.recipe
    assert len(job.result['pipeline']['input_integrity']['files']) == 6
    assert (source / 'report.json').read_bytes() == original_report
    assert (source / 'mix.wav').read_bytes() == original_mix
    assert len([item for item in calls if item == 'analyze']) >= 3


@pytest.mark.parametrize('change', ['modified', 'missing', 'report'])
def test_full_rebuild_blocks_modified_input_or_report(source_project, monkeypatch, tmp_path, change):
    import app.runtime_orchestrator as runtime_module
    _, _, _, calls = source_project
    monkeypatch.setattr(runtime_module, 'ROOT', tmp_path)
    source_input = tmp_path / 'input.wav'
    source_input.write_bytes(b'original')
    source = tmp_path / 'original'
    orchestrator.run_full_pipeline('src', {'references': [str(source_input)], 'voice_mode': 'off'}, out_root=source)
    runtime = RuntimeOrchestrator()
    runtime.stop()
    monkeypatch.setattr(runtime, '_ensure_worker', lambda: None)
    opened = runtime.open_project(source)
    if change == 'modified': source_input.write_bytes(b'changed!')
    if change == 'missing': source_input.unlink()
    if change == 'report':
        path = source / 'report.json'
        path.write_bytes(path.read_bytes() + b' ')
    count = calls.count('analyze')
    tid = runtime.enqueue_opened_rebuild(opened)
    runtime._process(runtime.jobs[tid])
    job = runtime.jobs[tid]
    assert job.status == 'error'
    assert calls.count('analyze') == count
    assert not (Path(job.project_dir) / 'input_files').exists()
    assert not list(Path(job.project_dir).glob('.inputs-*'))


def test_manifest_requires_unchanged_inputs_across_original_render(source_project, monkeypatch, tmp_path):
    _, _, _, _ = source_project
    audio = tmp_path / 'ref.wav'
    audio.write_bytes(b'original')
    def changed(*args, **kwargs):
        audio.write_bytes(b'modified')
        return {'ok': True, 'analysis': {'bpm': 100}}
    monkeypatch.setattr(orchestrator, '_stage_analyze', changed)
    report = orchestrator.run_full_pipeline('source', {'references': [str(audio)]}, out_root=tmp_path/'source')
    assert 'input_integrity' not in report
    assert any('inputs or recipe changed' in warning for warning in report['warnings'])


def test_legacy_snapshot_is_master_only_and_cannot_be_fully_rebuilt(source_project, monkeypatch, tmp_path):
    import app.runtime_orchestrator as runtime_module
    source, _, report, _ = source_project
    report.pop('input_integrity')
    (source / 'report.json').write_text(json.dumps(report), encoding='utf-8')
    monkeypatch.setattr(runtime_module, 'ROOT', tmp_path)
    runtime = RuntimeOrchestrator()
    runtime.stop()
    monkeypatch.setattr(runtime, '_ensure_worker', lambda: None)
    opened = runtime.open_project(source)
    with pytest.raises(ValueError, match='no input integrity'):
        runtime.enqueue_opened_rebuild(opened)


def test_frozen_inputs_relocate_with_the_project(source_project, monkeypatch, tmp_path):
    import shutil
    import app.runtime_orchestrator as runtime_module
    _, _, _, _ = source_project
    monkeypatch.setattr(runtime_module, 'ROOT', tmp_path)
    source = tmp_path / 'original-project'
    source.mkdir()
    input_path = source / 'my-input.wav'
    input_path.write_bytes(b'content')
    report = orchestrator.run_full_pipeline('src', {'references': [str(input_path)]}, out_root=source)
    assert 'input_integrity' in report
    moved = tmp_path/'moved-project'
    shutil.move(source, moved)
    runtime = RuntimeOrchestrator()
    runtime.stop()
    monkeypatch.setattr(runtime, '_ensure_worker', lambda: None)
    opened = runtime.open_project(moved)
    tid = runtime.enqueue_opened_rebuild(opened)
    runtime._process(runtime.jobs[tid])
    job = runtime.jobs[tid]
    assert job.status == 'done', job.error
    assert Path(job.recipe['references'][0]).read_bytes() == b'content'

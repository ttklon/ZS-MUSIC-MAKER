import numpy as np
import soundfile as sf

from app.core.orchestrator import run_full_pipeline
from app.core.stages.imported_beat import import_instrumental


def test_user_instrumental_is_used_by_mix_without_touching_source(tmp_path):
    source = tmp_path / "source.flac"
    signal = (0.15 * np.sin(np.arange(8000 * 2) * 0.12)).astype("float32")
    sf.write(source, signal, 8000)
    before = source.read_bytes()
    root = tmp_path / "project"
    result = run_full_pipeline("own-beat", {"beat_engine": "user_audio", "beat_input_path": str(source),
                                             "voice_mode": "off"}, out_root=root, only={"beat", "mix"})
    stages = {stage["name"]: stage for stage in result["stages"]}
    assert stages["_stage_beat"]["output"]["engine"] == "user_instrumental"
    assert stages["_stage_beat"]["status"] == "OK"
    assert stages["_stage_mix_and_sidechain"]["status"] == "OK"
    assert sf.info(root / "beat.wav").duration == 2
    assert source.read_bytes() == before


def test_silent_or_missing_input_fails_without_overwriting_existing_result(tmp_path):
    source = tmp_path / "silence.wav"
    sf.write(source, np.zeros(8000), 8000)
    dest = tmp_path / "beat.wav"
    dest.write_bytes(b"previous")
    import pytest
    with pytest.raises(ValueError, match="silent"):
        import_instrumental(str(source), dest)
    with pytest.raises(FileNotFoundError):
        import_instrumental(str(tmp_path / "missing.wav"), dest)
    assert dest.read_bytes() == b"previous"
    assert set(tmp_path.iterdir()) == {source, dest}


def test_recorded_backing_is_enforced_through_pipeline(tmp_path):
    from modules.release.export import sha256_file
    beat = tmp_path / "beat.wav"
    voice = tmp_path / "vocal.wav"
    sr = 8000
    t = np.arange(sr * 2) / sr
    sf.write(beat, .1 * np.sin(2 * np.pi * 220 * t), sr)
    sf.write(voice, .1 * np.sin(2 * np.pi * 440 * t), sr)
    before_voice = voice.read_bytes()
    sha = sha256_file(beat)
    state = {"beat_engine": "user_audio", "beat_input_path": str(beat), "recorded_backing_sha256": sha,
             "own_vocal_wav": str(voice), "use_rvc": False, "use_vocal_fx": False}
    good = run_full_pipeline("paired", state, out_root=tmp_path / "good", only={"beat", "vocal", "mix"})
    stages = {stage["name"]: stage for stage in good["stages"]}
    assert stages["_stage_beat"]["status"] == "OK" and stages["_stage_mix_and_sidechain"]["output"]["vocal_used"]
    sf.write(beat, .1 * np.sin(2 * np.pi * 330 * t), sr)
    bad = run_full_pipeline("changed", state, out_root=tmp_path / "bad", only={"beat", "vocal", "mix"})
    stages = {stage["name"]: stage for stage in bad["stages"]}
    assert stages["_stage_beat"]["status"] == "FAILED" and "recorded backing changed" in stages["_stage_beat"]["reason"]
    assert stages["_stage_mix_and_sidechain"]["status"] == "BLOCKED" and voice.read_bytes() == before_voice
    state["beat_engine"] = "procedural"
    changed = run_full_pipeline("procedural", state, out_root=tmp_path / "other", only={"beat", "mix"})
    beat_stage = next(x for x in changed["stages"] if x["name"] == "_stage_beat")
    assert beat_stage["status"] == "FAILED" and "recorded backing required" in beat_stage["reason"]


def test_recorded_backing_change_during_import_preserves_existing_output(tmp_path, monkeypatch):
    import pytest
    from modules.release import export
    beat = tmp_path / "beat.wav"
    target = tmp_path / "out.wav"
    sf.write(beat, np.full(8000, .1, dtype=np.float32), 8000)
    target.write_bytes(b"previous output")
    original = export.sha256_file(beat)
    hashes = iter((original, "0" * 64))
    monkeypatch.setattr(export, "sha256_file", lambda *args: next(hashes))
    with pytest.raises(ValueError, match="changed during import"):
        import_instrumental(str(beat), target, expected_sha256=original)
    assert target.read_bytes() == b"previous output"
    assert set(tmp_path.iterdir()) == {beat, target}


def test_import_never_replaces_source_or_hardlink(tmp_path):
    import pytest
    beat = tmp_path / "beat.wav"
    sf.write(beat, np.full(8000, .1, dtype=np.float32), 8000)
    original = beat.read_bytes()
    with pytest.raises(ValueError, match="different files"):
        import_instrumental(str(beat), beat)
    link = tmp_path / "link.wav"
    link.hardlink_to(beat)
    with pytest.raises(ValueError, match="different files"):
        import_instrumental(str(beat), link)
    assert beat.read_bytes() == original and link.read_bytes() == original


def test_recorded_backing_may_be_relocated_if_bytes_are_identical(tmp_path):
    import shutil
    from modules.release.export import sha256_file
    beat, moved, out = tmp_path / "beat.flac", tmp_path / "moved.flac", tmp_path / "out.wav"
    sf.write(beat, np.full(8000, .1, dtype=np.float32), 8000)
    digest = sha256_file(beat)
    shutil.copyfile(beat, moved)
    beat.unlink()
    result = import_instrumental(str(moved), out, expected_sha256=digest)
    assert result["ok"] and sf.info(out).frames == 8000

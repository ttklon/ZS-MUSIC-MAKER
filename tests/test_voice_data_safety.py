"""Voice archive persistence contracts; no real microphone or Windows claim."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import threading

import pytest

from modules import voice_convert, voice_index_store, voice_vault
from modules.voice_index_store import VoiceIndexError


def set_up_archive(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setattr(voice_convert, "VAULT_DIR", vault)
    monkeypatch.setattr(voice_convert, "VOICE_INDEX", vault / "vault_index.json")
    monkeypatch.setattr(voice_convert, "_ensure_dirs", lambda: None)
    monkeypatch.setattr(voice_vault, "VAULT_DIR", vault)
    monkeypatch.setattr(voice_vault, "INDEX_FILE", vault / "index.json")
    return vault


@pytest.mark.parametrize("bad", [b"{not json", b"{}", b"[1,2,3]"])
def test_gui_vault_bad_index_never_replaced(tmp_path, monkeypatch, bad):
    vault = set_up_archive(tmp_path, monkeypatch)
    index = vault / "vault_index.json"
    index.write_bytes(bad)
    source = vault / "singer.wav"
    source.write_bytes(b"irreplaceable take")
    result = voice_convert.add_recording(str(source), {"style": "singing", "duration_sec": 9})
    assert "error" in result and result["unindexed_path"] == str(source)
    assert index.read_bytes() == bad and source.read_bytes() == b"irreplaceable take"
    assert "error" in voice_convert.rate_recording(0, 5)
    with pytest.raises(VoiceIndexError):
        voice_convert.vault_summary()


def test_write_failure_keeps_old_index_and_unindexed_copy(tmp_path, monkeypatch):
    vault = set_up_archive(tmp_path, monkeypatch)
    index = vault / "vault_index.json"
    old = b'[{"file":"old.wav","style":"singing","duration_sec":4}]'
    index.write_bytes(old)
    source = tmp_path / "new.wav"
    source.write_bytes(b"new singer audio")
    monkeypatch.setattr(voice_index_store.os, "replace", lambda *a: (_ for _ in ()).throw(OSError("disk error")))
    result = voice_convert.add_recording(str(source), {"style": "singing"})
    assert "disk error" in result["error"] and index.read_bytes() == old
    assert Path(result["unindexed_path"]).read_bytes() == source.read_bytes()
    assert not list(vault.glob("*.tmp")) and not list(vault.glob(".*.tmp"))


def test_serialized_concurrent_recordings_do_not_lose_entries(tmp_path, monkeypatch):
    vault = set_up_archive(tmp_path, monkeypatch)
    def add(i):
        source = tmp_path / f"take{i}.wav"
        source.write_bytes(f"recording {i}".encode())
        return voice_convert.add_recording(str(source), {"style": "singing", "duration_sec": i + 1})
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(add, range(20)))
    assert all("error" not in item for item in results)
    items = json.loads((vault / "vault_index.json").read_text(encoding="utf-8"))
    assert len(items) == 20 and len({item["path"] for item in items}) == 20
    assert all(Path(item["path"]).is_file() for item in items)


def test_lock_timeout_is_explicit_and_existing_index_survives(tmp_path):
    index = tmp_path / "index.json"
    index.write_bytes(b"[]")
    locked, released = threading.Event(), threading.Event()
    def hold():
        with voice_index_store.lock_index(index):
            locked.set()
            assert released.wait(3)
    thread = threading.Thread(target=hold)
    thread.start()
    assert locked.wait(3)
    try:
        with pytest.raises(VoiceIndexError, match="locked"):
            with voice_index_store.lock_index(index, timeout=0.05):
                pass
    finally:
        released.set()
        thread.join(3)
    assert not thread.is_alive() and index.read_bytes() == b"[]"


def test_symlinked_index_is_refused_without_changing_target(tmp_path):
    target = tmp_path / "target.json"
    target.write_bytes(b"[]")
    index = tmp_path / "index.json"
    try:
        index.symlink_to(target)
    except OSError:
        pytest.skip("symlinks unavailable on this platform")
    with pytest.raises(VoiceIndexError, match="symbolic link"):
        voice_index_store.read_index(index, list, lambda data: isinstance(data, list))
    with pytest.raises(VoiceIndexError, match="symbolic link"):
        voice_index_store.write_index(index, [])
    assert target.read_bytes() == b"[]" and index.is_symlink()


def test_full_file_digest_distinguishes_takes_with_identical_start(tmp_path, monkeypatch):
    vault = set_up_archive(tmp_path, monkeypatch)
    first, second = tmp_path / "first.wav", tmp_path / "second.wav"
    prefix = b"x" * (1024 * 1024)
    first.write_bytes(prefix + b"part one")
    second.write_bytes(prefix + b"part two")
    one = voice_vault.add_recording(str(first))
    two = voice_vault.add_recording(str(second))
    assert one["ok"] and two["ok"] and one["item"]["id"] != two["item"]["id"]
    assert len(json.loads((vault / "index.json").read_text())["items"]) == 2
    assert voice_vault.add_recording(str(first))["already_indexed"]


def test_legacy_md5_duplicate_and_reindex_preserve_metadata(tmp_path, monkeypatch):
    vault = set_up_archive(tmp_path, monkeypatch)
    source = tmp_path / "record.wav"
    source.write_bytes(b"old voice")
    copied = vault / "old.wav"
    copied.write_bytes(source.read_bytes())
    mid = hashlib.md5(source.read_bytes()).hexdigest()
    old = {"id": mid, "vault_path": str(copied), "used_in_rvc_rounds": ["session-1"], "added_at": 123}
    (vault / "index.json").write_text(json.dumps({"items": {mid: old}}))
    duplicate = voice_vault.add_recording(str(source))
    assert duplicate["already_indexed"] and duplicate["item"] == old
    overwritten = voice_vault.add_recording(str(source), overwrite=True)
    assert overwritten["ok"] and overwritten["item"]["used_in_rvc_rounds"] == ["session-1"]
    assert overwritten["item"]["added_at"] == 123
    assert copied.read_bytes() == b"old voice"


@pytest.mark.parametrize("kind", ["content", "symlink", "hardlink"])
def test_existing_lock_path_never_overwrites_user_file(tmp_path, kind):
    import os
    index = tmp_path / "index.json"
    lock = tmp_path / "index.json.lock"
    target = tmp_path / "voice.wav"
    target.write_bytes(b"keep user audio")
    try:
        if kind == "content":
            lock.write_bytes(b"keep lock contents")
        elif kind == "symlink":
            lock.symlink_to(target)
        else:
            os.link(target, lock)
    except OSError:
        pytest.skip("links unavailable on this platform")
    with pytest.raises(VoiceIndexError, match="Unsafe existing"):
        with voice_index_store.lock_index(index):
            pass
    assert target.read_bytes() == b"keep user audio"
    if kind == "content":
        assert lock.read_bytes() == b"keep lock contents"


def test_nonfinite_metadata_cannot_corrupt_index(tmp_path, monkeypatch):
    vault = set_up_archive(tmp_path, monkeypatch)
    index = vault / "vault_index.json"
    index.write_bytes(b"[]")
    source = vault / "voice.wav"
    source.write_bytes(b"user data")
    result = voice_convert.add_recording(str(source), {"duration_sec": float("nan")})
    assert "error" in result and index.read_bytes() == b"[]" and source.read_bytes() == b"user data"
    index.write_bytes(b'[{"duration_sec": NaN}]')
    result = voice_convert.add_recording(str(source), {"duration_sec": 1})
    assert "error" in result and index.read_bytes() == b'[{"duration_sec": NaN}]'


def test_duration_and_typed_letters_are_not_claimed_as_trained_voice(tmp_path, monkeypatch):
    from modules import user_profile
    vault = set_up_archive(tmp_path, monkeypatch)
    (vault / "vault_index.json").write_text(json.dumps([{
        "file": "missing.wav", "style": "singing", "duration_sec": 600,
        "text": "всё было набрано вручную"}], ensure_ascii=False), encoding="utf-8")
    profile = tmp_path / "profile.json"
    raw = b'{"artist_name":"test", "voice_training_completed":true}'
    profile.write_bytes(raw)
    monkeypatch.setattr(user_profile, "PROFILE_FILE", profile)
    summary = voice_convert.vault_summary()
    assert summary["minimum_duration_met"] and not summary["ready_for_training"]
    assert summary["duration_kind"] == "index_metadata_unverified"
    assert summary["training_status"] == "UNVERIFIED" and not summary["audio_coverage_verified"]
    assert summary["coverage_kind"] == "entered_letters_not_asr"
    progress = user_profile.sync_voice_progress()
    assert progress["hours"] == 0.17 and progress["hours_kind"] == "recorded_audio_not_training"
    assert not progress["ready"] and not progress["profile_updated"] and progress["training_status"] == "UNVERIFIED"
    assert profile.read_bytes() == raw


@pytest.mark.parametrize("archive", ["wizard", "vault"])
def test_interrupted_copy_reports_original_not_partial_as_saved_take(tmp_path, monkeypatch, archive):
    from modules import voice_vault
    vault = set_up_archive(tmp_path, monkeypatch)
    monkeypatch.setattr(voice_vault, "VAULT_DIR", vault)
    monkeypatch.setattr(voice_vault, "INDEX_FILE", vault / "index.json")
    source = tmp_path / "source.wav"
    source.write_bytes(b"original voice bytes")
    def interrupted(src, dst):
        dst.write(src.read(3))
        raise OSError("disk full")
    monkeypatch.setattr(voice_convert.shutil, "copyfileobj", interrupted)
    result = (voice_convert.add_recording(str(source), {}) if archive == "wizard"
              else voice_vault.add_recording(str(source)))
    assert "error" in result and Path(result["unindexed_path"]) == source
    assert source.read_bytes() == b"original voice bytes"
    partial = Path(result["partial_copy_path"])
    assert partial.read_bytes() == b"ori" and partial != source


def test_recording_index_checks_source_copy_and_expected_hash(tmp_path, monkeypatch):
    vault = set_up_archive(tmp_path, monkeypatch)
    source = tmp_path / 'singer.wav'
    source.write_bytes(b'original take')
    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    result = voice_convert.add_recording(str(source), {'recording_sha256': expected, 'style': 'singing'})
    assert result['recording_sha256'] == expected
    assert hashlib.sha256(Path(result['path']).read_bytes()).hexdigest() == expected
    source.write_bytes(b'changed take')
    failed = voice_convert.add_recording(str(source), {'recording_sha256': expected})
    assert 'changed' in failed['error']
    assert len(json.loads((vault / 'vault_index.json').read_text())) == 1
    assert source.read_bytes() == b'changed take'


def test_corrupted_archive_copy_is_not_indexed_or_deleted(tmp_path, monkeypatch):
    vault = set_up_archive(tmp_path, monkeypatch)
    source = tmp_path / 'singer.wav'
    source.write_bytes(b'original take')
    def corrupt(src, dest):
        dest.write(b'corrupt copy')
    monkeypatch.setattr(voice_convert.shutil, 'copyfileobj', corrupt)
    result = voice_convert.add_recording(str(source), {})
    assert 'integrity' in result['error']
    assert Path(result['partial_copy_path']).read_bytes() == b'corrupt copy'
    assert source.read_bytes() == b'original take'
    assert not (vault / 'vault_index.json').exists()

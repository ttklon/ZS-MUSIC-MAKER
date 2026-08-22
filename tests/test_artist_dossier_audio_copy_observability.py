"""Regression coverage for Artist Dossier audio-copy diagnostics."""

from modules.artist_dossier import manager as dossier_manager


def test_add_track_persists_successful_audio_copy_diagnostics(tmp_path):
    root = tmp_path / "dossiers"
    source = tmp_path / "source.wav"
    source.write_bytes(b"wav")
    manager = dossier_manager.DossierManager(root=root)

    track = manager.add_track("Artist", "Song", audio_path=str(source))

    copied = root / "artist" / "audio" / f"{track.track_id}.wav"
    assert track.audio_path == str(copied)
    assert track.audio_copy == {"ok": True, "source": str(source), "path": str(copied)}
    assert copied.read_bytes() == b"wav"
    assert manager._load_track("artist", track.track_id).audio_copy == track.audio_copy


def test_add_track_keeps_source_and_persists_failed_audio_copy(monkeypatch, tmp_path):
    root = tmp_path / "dossiers"
    source = tmp_path / "source.wav"
    source.write_bytes(b"wav")
    manager = dossier_manager.DossierManager(root=root)

    def fail_copy(source_path, destination_path):
        raise OSError("disk full")

    monkeypatch.setattr(dossier_manager.shutil, "copy2", fail_copy)

    track = manager.add_track("Artist", "Song", audio_path=str(source))

    assert track.audio_path == str(source)
    assert track.audio_copy == {
        "ok": False,
        "source": str(source),
        "path": str(root / "artist" / "audio" / f"{track.track_id}.wav"),
        "error": "OSError: disk full",
    }
    assert manager._load_track("artist", track.track_id).audio_copy == track.audio_copy

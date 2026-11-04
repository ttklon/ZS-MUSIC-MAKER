"""Binding metadata must not be silently erased by duplicate archive entries."""
import pytest

from modules import voice_convert
from modules.voice_index_store import VoiceIndexError


def test_duplicate_unbound_entries_do_not_mask_recorded_backing(tmp_path, monkeypatch):
    take = str(tmp_path/'voice.wav')
    entries = [{'path': take, 'backing_path': '/beat.wav', 'backing_sha256': 'a'*64},
               {'path': take, 'backing_path': '', 'backing_sha256': ''}]
    monkeypatch.setattr(voice_convert, '_load_index', lambda: entries)
    assert voice_convert.recording_backing(take) == {'path': '/beat.wav', 'sha256': 'a'*64}


def test_conflicting_or_incomplete_duplicate_bindings_fail_closed(tmp_path, monkeypatch):
    take = str(tmp_path/'voice.wav')
    entries = [{'path': take, 'backing_path': '/beat.wav', 'backing_sha256': 'a'*64},
               {'path': take, 'backing_path': '/other.wav', 'backing_sha256': 'b'*64}]
    monkeypatch.setattr(voice_convert, '_load_index', lambda: entries)
    with pytest.raises(VoiceIndexError, match='conflicting'):
        voice_convert.recording_backing(take)
    entries[1]['backing_sha256'] = ''
    with pytest.raises(VoiceIndexError, match='incomplete'):
        voice_convert.recording_backing(take)

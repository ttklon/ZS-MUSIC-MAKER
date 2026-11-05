"""Binding metadata must not be silently erased by duplicate archive entries."""
import pytest

from modules import voice_convert
from modules.voice_index_store import VoiceIndexError


def test_duplicate_unbound_entries_do_not_mask_recorded_backing(tmp_path, monkeypatch):
    take = str(tmp_path/'voice.wav')
    entries = [{'path': take, 'backing_path': '/beat.wav', 'backing_sha256': 'a'*64},
               {'path': take, 'backing_path': '', 'backing_sha256': ''}]
    monkeypatch.setattr(voice_convert, '_load_index', lambda: entries)
    assert voice_convert.recording_backing(take) == {'path': '/beat.wav', 'sha256': 'a'*64,
                                                      'binding_integrity': 'LEGACY_UNVERIFIED'}


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


def test_unbound_fingerprint_cannot_upgrade_legacy_binding(tmp_path, monkeypatch):
    take = str(tmp_path/'voice.wav')
    entries = [{'path': take, 'backing_path': '/beat.wav', 'backing_sha256': 'a'*64},
               {'path': take, 'recording_sha256': 'b'*64}]
    monkeypatch.setattr(voice_convert, '_load_index', lambda: entries)
    result = voice_convert.recording_backing(take)
    assert result['recording_sha256'] == 'b'*64
    assert result['binding_integrity'] == 'LEGACY_UNVERIFIED'
    entries[0]['recording_sha256'] = 'b'*64
    assert voice_convert.recording_backing(take)['binding_integrity'] == 'RECORDED_HASH'
    entries[1]['recording_sha256'] = 'c'*64
    with pytest.raises(VoiceIndexError, match='conflicting vocal'):
        voice_convert.recording_backing(take)


@pytest.mark.parametrize('invalid', ['bad', 0, False, [], 'A'*64])
def test_invalid_vocal_fingerprints_fail_closed(tmp_path, monkeypatch, invalid):
    take = str(tmp_path/'voice.wav')
    monkeypatch.setattr(voice_convert, '_load_index', lambda: [{'path': take, 'recording_sha256': invalid}])
    with pytest.raises(VoiceIndexError, match='invalid vocal'):
        voice_convert.recording_backing(take)


@pytest.mark.parametrize('field,value', [('backing_path', 0), ('backing_sha256', False), ('backing_path', [])])
def test_invalid_falsy_backing_metadata_is_not_unbound(tmp_path, monkeypatch, field, value):
    take = str(tmp_path/'voice.wav')
    monkeypatch.setattr(voice_convert, '_load_index', lambda: [{'path': take, field: value}])
    with pytest.raises(VoiceIndexError, match='invalid backing'):
        voice_convert.recording_backing(take)

"""Replacement copies, safety and binding contracts; no GUI or real-device claims."""
import hashlib
import shutil
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from app.core.input_integrity import capture_inputs, freeze_inputs
from app.core.project_inputs import prepare_replacements
from modules import voice_convert


def wave(path, hz=220, duration=0.5):
    samples = np.sin(2 * np.pi * hz * np.arange(int(8000 * duration)) / 8000) * 0.3
    sf.write(path, samples, 8000)
    return path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr(voice_convert, 'recording_backing', lambda _: {})
    source, dest = tmp_path/'source', tmp_path/'destination'
    source.mkdir(); dest.mkdir()
    beat = wave(source/'beat.wav', 150)
    voice = wave(source/'voice.wav', 300)
    ref = wave(source/'ref.wav', 400)
    recipe = {'references': [str(ref)], 'beat_input_path': str(beat), 'beat_engine': 'user_audio',
              'own_vocal_wav': str(voice), 'voice_mode': 'pro', 'recorded_backing_sha256': digest(beat)}
    report = {'input_integrity': capture_inputs(recipe), 'project_root': str(source)}
    return source, dest, recipe, report


def execute(project, replacements):
    source, dest, recipe, report = project
    details = {}
    result = freeze_inputs(recipe, report, source, dest, prepare_replacements(replacements), details)
    return result, details


def test_replace_multiple_references_skips_missing_old_and_preserves_other_inputs(project, tmp_path):
    source, dest, recipe, _ = project
    old_voice = Path(recipe['own_vocal_wav']).read_bytes()
    Path(recipe['references'][0]).unlink()
    refs = [wave(tmp_path/'new-a.wav', 100), wave(tmp_path/'new-b.flac', 500)]
    result, detail = execute(project, {'references': [str(p) for p in refs]})
    assert [digest(p) for p in result['references']] == [digest(p) for p in refs]
    assert Path(result['own_vocal_wav']).read_bytes() == old_voice
    assert result['recorded_backing_sha256'] == recipe['recorded_backing_sha256']
    assert detail == {'replaced_fields': ['references']}
    assert all(Path(p).parent == dest/'input_files' for p in result['references'])
    assert not (source/'ref.wav').exists() and Path(recipe['own_vocal_wav']).read_bytes() == old_voice


def test_reference_removal_is_explicit_and_other_inputs_still_verified(project):
    result, detail = execute(project, {'references': []})
    assert result['references'] == [] and detail == {'replaced_fields': ['references']}
    assert Path(result['own_vocal_wav']).exists()


def test_new_backing_never_drops_existing_voice_binding(project, tmp_path):
    source, dest, recipe, _ = project
    replacement = wave(tmp_path/'different.wav', 200)
    with pytest.raises(ValueError, match='does not match'):
        execute(project, {'beat_input_path': str(replacement), 'ack_unverified_pairing': True})
    assert not list(dest.iterdir())
    assert digest(recipe['beat_input_path']) == recipe['recorded_backing_sha256']
    assert Path(recipe['own_vocal_wav']).is_file()


def test_same_backing_copy_retains_binding_even_when_original_missing(project, tmp_path):
    _, _, recipe, _ = project
    replacement = tmp_path/'same.wav'
    shutil.copyfile(recipe['beat_input_path'], replacement)
    Path(recipe['beat_input_path']).unlink()
    result, detail = execute(project, {'beat_input_path': str(replacement)})
    assert result['recorded_backing_sha256'] == digest(replacement)
    assert detail['vocal_binding'] == 'PRESERVED'


def test_unbound_new_take_needs_confirmation_and_clears_old_binding(project, tmp_path):
    _, dest, recipe, _ = project
    take = wave(tmp_path/'new_voice.wav', 600)
    with pytest.raises(ValueError, match='explicit confirmation'):
        execute(project, {'own_vocal_wav': str(take)})
    assert not list(dest.iterdir())
    result, detail = execute(project, {'own_vocal_wav': str(take), 'ack_unverified_pairing': True})
    assert result['recorded_backing_sha256'] == ''
    assert detail['vocal_binding'] == 'UNVERIFIED'
    assert digest(result['own_vocal_wav']) == digest(take)
    assert digest(result['beat_input_path']) == recipe['recorded_backing_sha256']


def test_same_voice_bytes_do_not_erase_known_binding(project, tmp_path):
    _, dest, recipe, _ = project
    take = tmp_path/'same_voice.wav'
    shutil.copyfile(recipe['own_vocal_wav'], take)
    wrong = wave(tmp_path/'wrong.wav', 800)
    with pytest.raises(ValueError, match='does not match'):
        execute(project, {'own_vocal_wav': str(take), 'beat_input_path': str(wrong),
                          'ack_unverified_pairing': True})
    assert not list(dest.iterdir())


def test_indexed_recording_pair_matches_or_fails(project, tmp_path, monkeypatch):
    _, dest, _, _ = project
    take = wave(tmp_path/'take.wav', 600)
    beat = wave(tmp_path/'newbeat.wav', 500)
    monkeypatch.setattr(voice_convert, 'recording_backing', lambda _: {'path': str(beat), 'sha256': digest(beat)})
    with pytest.raises(ValueError, match='does not match'):
        execute(project, {'own_vocal_wav': str(take), 'ack_unverified_pairing': True})
    assert not list(dest.iterdir())
    result, detail = execute(project, {'own_vocal_wav': str(take), 'beat_input_path': str(beat)})
    assert detail['vocal_binding'] == 'ARCHIVE_BACKING_MATCH'
    assert result['recorded_backing_sha256'] == digest(beat)
    assert digest(result['beat_input_path']) == digest(beat)


def test_incomplete_or_unreadable_archive_never_becomes_unbound(project, tmp_path, monkeypatch):
    _, dest, _, _ = project
    take = wave(tmp_path/'take.wav', 600)
    monkeypatch.setattr(voice_convert, 'recording_backing', lambda _: {'path': 'x', 'sha256': ''})
    with pytest.raises(ValueError, match='incomplete'):
        execute(project, {'own_vocal_wav': str(take), 'ack_unverified_pairing': True})
    assert not list(dest.iterdir())
    def fail(_): raise voice_convert.VoiceIndexError('corrupt index')
    monkeypatch.setattr(voice_convert, 'recording_backing', fail)
    with pytest.raises(voice_convert.VoiceIndexError):
        execute(project, {'own_vocal_wav': str(take), 'ack_unverified_pairing': True})
    assert not list(dest.iterdir())


def test_unbound_existing_voice_and_changed_backing_needs_ack(project, tmp_path):
    _, dest, recipe, report = project
    recipe['recorded_backing_sha256'] = ''
    report['input_integrity'] = capture_inputs(recipe)
    beat = wave(tmp_path/'beat2.wav', 500)
    with pytest.raises(ValueError, match='explicit confirmation'):
        execute(project, {'beat_input_path': str(beat)})
    assert not list(dest.iterdir())
    result, detail = execute(project, {'beat_input_path': str(beat), 'ack_unverified_pairing': True})
    assert result['recorded_backing_sha256'] == '' and detail['vocal_binding'] == 'UNVERIFIED'


def test_selected_file_changed_after_queue_fails_and_cleans_up(project, tmp_path):
    source, dest, recipe, report = project
    ref = wave(tmp_path/'new.wav', 500)
    selection = prepare_replacements({'references': [str(ref)]})
    wave(ref, 700)
    with pytest.raises(ValueError, match='changed since queueing'):
        freeze_inputs(recipe, report, source, dest, selection)
    assert not list(dest.iterdir())


def test_invalid_or_corrupted_replacement_and_unselected_input_fail_closed(project, tmp_path):
    _, dest, recipe, _ = project
    invalid = tmp_path/'invalid.wav'
    invalid.write_bytes(b'not audio')
    with pytest.raises(ValueError):
        execute(project, {'references': [str(invalid)]})
    assert not list(dest.iterdir())
    ref = wave(tmp_path/'new.wav', 500)
    Path(recipe['own_vocal_wav']).write_bytes(b'changed')
    with pytest.raises(ValueError, match='integrity'):
        execute(project, {'references': [str(ref)]})
    assert not list(dest.iterdir())


def test_disk_full_during_new_copy_cleans_temporary_and_preserves_sources(project, tmp_path, monkeypatch):
    import app.core.project_inputs as inputs
    _, dest, recipe, _ = project
    replacement = wave(tmp_path/'new.wav', 500)
    real_copy = inputs.shutil.copyfile
    def fail_new(src, dst):
        if Path(src) == replacement:
            Path(dst).write_bytes(b'partial')
            raise OSError('disk full')
        return real_copy(src, dst)
    monkeypatch.setattr(inputs.shutil, 'copyfile', fail_new)
    with pytest.raises(OSError, match='disk full'):
        execute(project, {'references': [str(replacement)]})
    assert not list(dest.iterdir())
    assert replacement.is_file() and Path(recipe['own_vocal_wav']).is_file()


@pytest.mark.parametrize('bad', [{'rvc_model_path': '/a.wav'}, {'references': 'a.wav'},
    {'references': ['relative.wav']}, {'references': ['/a.mp3']}, {'ack_unverified_pairing': 1},
    {'ack_unverified_pairing': True}, {'references': ['x'] * 51}, []])
def test_invalid_selection_is_rejected(bad):
    with pytest.raises((ValueError, OSError)):
        prepare_replacements(bad)

"""Replacement regressions for moved projects and re-opened recipes."""
import shutil
from pathlib import Path

import pytest

from app.core.input_integrity import capture_inputs, freeze_inputs
from app.core.project_inputs import prepare_replacements
from app.core.project_snapshot import restore_recipe, snapshot_recipe
from modules import voice_convert
from test_project_input_replacements import digest, wave


def test_moved_project_retains_unreplaced_files_and_replacement_can_be_reopened(tmp_path, monkeypatch):
    monkeypatch.setattr(voice_convert, 'recording_backing', lambda _: {})
    source, dest = tmp_path/'original', tmp_path/'next'
    source.mkdir(); dest.mkdir()
    beat, voice = wave(source/'beat.wav', 100), wave(source/'voice.wav', 200)
    old_ref = wave(source/'ref.wav', 300)
    recipe = {'references': [str(old_ref)], 'beat_input_path': str(beat), 'beat_engine': 'user_audio',
              'vocal_wav': str(voice), 'voice_mode': ' OFF ', 'recorded_backing_sha256': digest(beat)}
    report = {'project_root': str(source), 'input_integrity': capture_inputs(recipe)}
    moved = tmp_path/'moved'
    source.rename(moved)
    new_voice = wave(tmp_path/'new.wav', 700)
    selection = prepare_replacements({'own_vocal_wav': str(new_voice), 'references': [], 'ack_unverified_pairing': True})
    details = {}
    result = freeze_inputs(recipe, report, moved, dest, selection, details)
    assert result['voice_mode'] == 'pro' and 'vocal_wav' not in result
    assert result['recorded_backing_sha256'] == '' and result['references'] == []
    assert digest(result['beat_input_path']) == digest(moved/'beat.wav')
    assert digest(result['own_vocal_wav']) == digest(new_voice)
    assert details['vocal_binding'] == 'UNVERIFIED'
    # Simulate reopening from the new report: retained/new paths now have a full manifest.
    report2 = {'project_root': str(dest), 'desktop_recipe_snapshot': snapshot_recipe(result),
               'input_integrity': capture_inputs(result)}
    dest2 = tmp_path/'again'; dest2.mkdir()
    restored = freeze_inputs(restore_recipe(report2), report2, dest, dest2)
    assert digest(restored['own_vocal_wav']) == digest(new_voice)
    assert digest(restored['beat_input_path']) == digest(moved/'beat.wav')
    assert restored['recorded_backing_sha256'] == ''


def test_symlink_replacement_and_symlink_swap_after_queue_fail(tmp_path):
    file = wave(tmp_path/'file.wav')
    link = tmp_path/'link.wav'
    try:
        link.symlink_to(file)
    except OSError:
        pytest.skip('symlink creation unavailable')
    with pytest.raises(ValueError, match='regular'):
        prepare_replacements({'own_vocal_wav': str(link)})
    selected = prepare_replacements({'references': [str(file)]})
    moved = tmp_path/'moved.wav'
    shutil.move(file, moved)
    file.symlink_to(moved)
    source, dest = tmp_path/'source', tmp_path/'dest'
    source.mkdir(); dest.mkdir()
    recipe = {'references': []}
    report = {'input_integrity': capture_inputs(recipe)}
    with pytest.raises(ValueError, match='regular'):
        freeze_inputs(recipe, report, source, dest, selected)
    assert not list(dest.iterdir())

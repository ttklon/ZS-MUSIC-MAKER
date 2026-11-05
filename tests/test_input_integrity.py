"""Input manifest and copy tests: checksums detect changes, not authenticity."""
import copy
from pathlib import Path

import pytest

from app.core.input_integrity import capture_inputs, freeze_inputs, begin_input_capture, finish_input_capture


def setup_inputs(tmp_path):
    source = tmp_path / 'source'
    destination = tmp_path / 'destination'
    source.mkdir()
    destination.mkdir()
    input_path = source / 'voice.wav'
    input_path.write_bytes(b'not audio, tests file integrity only')
    recipe = {'own_vocal_wav': str(input_path), 'references': [str(input_path)], 'theme': 'тест'}
    manifest = capture_inputs(recipe)
    report = {'input_integrity': manifest, 'project_root': str(source)}
    return source, destination, input_path, recipe, report


def test_duplicate_inputs_are_copied_once(tmp_path):
    source, dest, path, recipe, report = setup_inputs(tmp_path)
    restored = freeze_inputs(recipe, report, source, dest)
    assert restored['own_vocal_wav'] == restored['references'][0]
    assert len(list((dest/'input_files').iterdir())) == 1
    assert Path(restored['own_vocal_wav']).read_bytes() == path.read_bytes()


@pytest.mark.parametrize('tamper', ['recipe', 'count', 'digest', 'path', 'version', 'index'])
def test_inconsistent_manifest_is_rejected(tmp_path, tamper):
    source, dest, path, recipe, report = setup_inputs(tmp_path)
    altered = copy.deepcopy(report)
    if tamper == 'recipe': recipe['theme'] = 'other'
    elif tamper == 'count': altered['input_integrity']['files'].pop()
    elif tamper == 'digest': altered['input_integrity']['files'][0]['sha256'] = 'z' * 64
    elif tamper == 'path': altered['input_integrity']['files'][0]['absolute_path'] = 'relative.wav'
    elif tamper == 'version': altered['input_integrity']['version'] = True
    elif tamper == 'index': altered['input_integrity']['files'][0]['index'] = 4
    with pytest.raises(ValueError):
        freeze_inputs(recipe, altered, source, dest)
    assert not (dest/'input_files').exists()
    assert path.read_bytes() == b'not audio, tests file integrity only'


def test_contained_input_cannot_escape_project_via_symlink(tmp_path):
    source, dest, path, recipe, report = setup_inputs(tmp_path)
    outsider = tmp_path/'external.wav'
    outsider.write_bytes(path.read_bytes())
    path.unlink()
    try:
        path.symlink_to(outsider)
    except OSError:
        pytest.skip('symlink creation unavailable')
    with pytest.raises(ValueError, match='escaped'):
        freeze_inputs(recipe, report, source, dest)
    assert outsider.read_bytes() == b'not audio, tests file integrity only'


def test_source_and_destination_must_not_overlap(tmp_path):
    source, _, _, recipe, report = setup_inputs(tmp_path)
    with pytest.raises(ValueError, match='separate'):
        freeze_inputs(recipe, report, source, source)
    child = source / 'child'
    child.mkdir()
    with pytest.raises(ValueError, match='separate'):
        freeze_inputs(recipe, report, source, child)


def test_missing_input_does_not_break_original_render_but_disables_rebuild(tmp_path):
    recipe = {'references': [str(tmp_path/'missing.wav')]}
    capture = begin_input_capture(recipe, True)
    report, warnings = {}, []
    finish_input_capture(report, recipe, capture, warnings)
    assert 'input_integrity' not in report
    assert warnings and 'full rebuild after reopening unavailable' in warnings[0]


def test_copy_corruption_rejected_without_leaking_partial_files(tmp_path, monkeypatch):
    import app.core.input_integrity as integrity
    source, dest, path, recipe, report = setup_inputs(tmp_path)
    def corrupt(src, dst):
        Path(dst).write_bytes(b'corrupted')
    monkeypatch.setattr(integrity.shutil, 'copyfile', corrupt)
    with pytest.raises(ValueError, match='copied input failed integrity'):
        freeze_inputs(recipe, report, source, dest)
    assert not list(dest.iterdir())
    assert path.read_bytes() == b'not audio, tests file integrity only'


def test_missing_after_reopen_never_uses_another_file_with_same_name(tmp_path):
    source, dest, path, recipe, report = setup_inputs(tmp_path)
    path.unlink()
    elsewhere = tmp_path/'other'/'voice.wav'
    elsewhere.parent.mkdir()
    elsewhere.write_bytes(b'not audio, tests file integrity only')
    with pytest.raises(ValueError, match='missing'):
        freeze_inputs(recipe, report, source, dest)
    assert not list(dest.iterdir())


def test_disk_full_during_copy_keeps_original_and_removes_partial(tmp_path, monkeypatch):
    import app.core.input_integrity as integrity
    source, dest, path, recipe, report = setup_inputs(tmp_path)
    def no_space(src, dst):
        Path(dst).write_bytes(b'partial')
        raise OSError('no space left')
    monkeypatch.setattr(integrity.shutil, 'copyfile', no_space)
    with pytest.raises(OSError, match='no space'):
        freeze_inputs(recipe, report, source, dest)
    assert not list(dest.iterdir())
    assert path.read_bytes() == b'not audio, tests file integrity only'

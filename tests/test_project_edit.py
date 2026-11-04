"""Project edits are explicit, bounded and cannot replace source files."""
import pytest
from app.core.project_edit import apply_project_overrides, validate_project_overrides


def test_edit_does_not_mutate_original_recipe_or_caller_changes():
    source = {'artist': 'old', 'artist_name': 'old', 'theme': 'old theme',
              'references': ['a.wav', 'b.wav'], 'own_vocal_wav': 'voice.wav',
              'recorded_backing_sha256': 'a' * 64, 'user_lyrics_lines': ['original']}
    changes = {'artist': 'new', 'theme': 'new theme', 'user_lyrics_lines': ['new', 'line'],
               'vocal_offset_ms': -125, 'export_stems': False}
    result = apply_project_overrides(source, changes)
    assert source['artist'] == 'old' and source['user_lyrics_lines'] == ['original']
    assert result['artist'] == result['artist_name'] == 'new'
    assert result['theme'] == 'new theme' and result['vocal_offset_ms'] == -125
    assert result['references'] == ['a.wav', 'b.wav'] and result['own_vocal_wav'] == 'voice.wav'
    assert result['recorded_backing_sha256'] == 'a' * 64 and result['export_stems'] is False
    changes['user_lyrics_lines'][0] = 'mutated'
    assert result['user_lyrics_lines'] == ['new', 'line']


@pytest.mark.parametrize('bad', [
    {'references': ['other.wav']}, {'own_vocal_wav': 'other.wav'}, {'beat_input_path': 'other.wav'},
    {'recorded_backing_sha256': ''}, {'voice_mode': 'off'}, {'only': ['master']},
    {'theme': ''}, {'theme': ' '}, {'theme': 12}, {'artist': ''},
    {'bpm_override': 221}, {'bpm_override': 0}, {'bpm_override': True},
    {'vocal_offset_ms': -5001}, {'vocal_offset_ms': 1.2}, {'n_verses': 0},
    {'export_stems': 1}, {'user_lyrics_lines': 'not a list'}, {'user_lyrics_lines': [3]},
    {'user_lyrics_lines': ['x' * 10001]}, {'trend_notes': 'x' * 100001},
    [], 'not a dict',
])
def test_invalid_edits_are_rejected(bad):
    with pytest.raises(ValueError):
        validate_project_overrides(bad)


def test_explicitly_clearing_lyrics_and_automatic_bpm_is_supported():
    assert validate_project_overrides({'user_lyrics_lines': [], 'bpm_override': None,
                                       'user_extra_prompt': '', 'reference_lyrics': ''}) == {
        'user_lyrics_lines': [], 'bpm_override': None, 'user_extra_prompt': '', 'reference_lyrics': ''}

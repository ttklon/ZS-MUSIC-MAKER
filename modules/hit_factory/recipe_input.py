"""Canonical snapshot-backed recipe input; explicit inputs override adaptive defaults."""
from __future__ import annotations

from app.core.project_snapshot import snapshot_recipe


def factory_recipe(recipe: dict, build_state, rng, *, strict=True) -> dict:
    state = snapshot_recipe(recipe)['recipe']
    if strict:
        validate_recipe_input(state)
    base = build_state(
        genre=state.get('genre') or '', theme=state.get('theme') or '',
        bpm_override=state.get('bpm_override'), aggression=state.get('aggression'),
        seed=state.get('seed'), duration_sec=state.get('duration_sec'), rng=rng,
    )
    for key, value in state.items():
        if (value is None and key in ('seed', 'bpm_override', 'duration_sec', 'aggression', 'genre', 'theme')) or (key in ('genre', 'theme') and value == ''):
            continue  # None means auto; preserve the resolved value, not another random choice.
        base[key] = value
    return snapshot_recipe(base)['recipe']


def validate_recipe_input(state: dict) -> None:
    """The new explicit API refuses ambiguous types; legacy UI normalization stays compatible."""
    for key in ('genre', 'theme', 'artist', 'reference_lyrics', 'own_vocal_wav',
                'beat_engine', 'musicgen_model', 'musicgen_device'):
        if key in state and not isinstance(state[key], str):
            raise ValueError(f'{key} must be a string')
    for key, lo, hi in (('seed', 0, 2**32 - 1), ('bpm_override', 40, 300),
                        ('duration_sec', 1, 3600), ('n_verses', 1, 4)):
        value = state.get(key)
        if value is not None and (type(value) is not int or not lo <= value <= hi):
            raise ValueError(f'{key} must be an integer in {lo}..{hi}')
    for key in ('references', 'user_lyrics_lines'):
        if key in state and (not isinstance(state[key], list) or
                             any(not isinstance(v, str) for v in state[key])):
            raise ValueError(f'{key} must be a list of strings')
    for key in ('use_rvc', 'bilingual'):
        if key in state and type(state[key]) is not bool:
            raise ValueError(f'{key} must be boolean')
    if 'style_vector' in state and not isinstance(state['style_vector'], dict):
        raise ValueError('style_vector must be an object')

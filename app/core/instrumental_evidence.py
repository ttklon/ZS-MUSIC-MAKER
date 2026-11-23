"""Narrow live producer provenance, not AI listening, quality or singing certification.

Hashes detect changed files, not a malicious producer or hostile filesystem races.
No legacy report is upgraded by this module: canonical finalization supplies live
stage objects and the caller's normalized recipe after the real render.
"""
from pathlib import Path
import re

from app.pipeline.artifact import inspect_audio
from app.pipeline import StageStatus


REVISION = 'classic-procedural-chain-v1'


def _stage_output(stages, name):
    matches = [s for s in stages if s.name == name]
    if len(matches) != 1 or matches[0].status != StageStatus.OK:
        raise ValueError(f'No unique successful live stage: {name}')
    output = matches[0].output
    if not isinstance(output, dict) or output.get('ok') is not True:
        raise ValueError(f'Invalid stage output: {name}')
    if any(output.get(k) for k in ('fallback_used', 'synthetic', 'placeholder', 'dry_run', 'reused', 'reused_from_project')):
        raise ValueError(f'Fallback/simulated/reused stage cannot supply new evidence: {name}')
    return output


def _asset(path, root, expected):
    if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
        raise ValueError('Missing or malformed production hash')
    candidate = Path(path)
    if candidate.is_symlink() or not candidate.resolve(strict=True).is_relative_to(root.resolve(strict=True)):
        raise ValueError('Evidence asset must be a regular local project file')
    audio = inspect_audio(str(candidate))
    if not audio['valid'] or audio['channels'] != 2:
        raise ValueError('Evidence requires valid stereo audio')
    if audio['sha256'] != expected:
        raise ValueError('Evidence asset changed after production')
    return audio


def _build(report, stages, root):
    beat = _stage_output(stages, '_stage_beat')
    mix = _stage_output(stages, '_stage_mix_and_sidechain')
    _stage_output(stages, '_stage_mastering')
    _stage_output(stages, '_stage_polish')
    if beat.get('engine') != 'beat_constructor.construct_beat' or not beat.get('sections'):
        raise ValueError('Only actual structured procedural beat-constructor output is covered')
    if mix.get('engine') != 'modules.mix.bus' or mix.get('vocal_used') is not False or mix.get('gates_passed') is not True:
        raise ValueError('Not a validated instrumental mix')
    trace = mix.get('source_trace') or {}
    if trace.get('schema') != 1 or trace.get('vocal_requested') is not False:
        raise ValueError('Missing instrumental input-to-mix identity trace')
    beat_audio = _asset(beat['path'], root, trace['beat']['sha256'])
    mix_audio = _asset(mix['out_wav'], root, trace['mix']['sha256'])
    master_record = report['artifact_integrity']['master']
    master = _asset(report['master_path'], root, master_record['sha256'])
    if max(a['seconds'] for a in (beat_audio, mix_audio, master)) - min(a['seconds'] for a in (beat_audio, mix_audio, master)) > 0.1:
        raise ValueError('Production chain duration mismatch')
    return {'schema': 1, 'kind': 'instrumental', 'engine': 'classic_procedural_instrumental',
            'revision': REVISION, 'master_sha256': master['sha256'], 'checks': {'music_present': True},
            'evidence_method': 'live_producer_trace_not_listening_test',
            'assets': {'beat': beat_audio['sha256'], 'mix': mix_audio['sha256'], 'master': master['sha256']}}


def attach_instrumental_evidence(report, recipe, stages, root):
    if (recipe.get('voice_mode') != 'off' or recipe.get('beat_engine') != 'procedural'
            or recipe.get('use_texture') is not False or recipe.get('export_stems') is not False):
        return
    report.pop('render_evidence', None)
    if (report.get('outcome') or {}).get('succeeded') is not True or report.get('dry_run') or report.get('only') or report.get('revision'):
        return
    try:
        report['render_evidence'] = _build(report, stages, root)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        report['content_evidence_unavailable'] = f'{type(exc).__name__}: {exc}'

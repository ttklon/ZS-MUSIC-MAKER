"""Real small WAV fixtures test classification, NOT music quality or singing inference."""
from __future__ import annotations

import math
import struct
import wave

import pytest

from app.pipeline.artifact import inspect_audio
from app.pipeline.result import CHECKS, assess_result


@pytest.fixture
def audio(tmp_path):
    target = tmp_path / 'fixture.wav'
    with wave.open(str(target), 'wb') as out:
        out.setparams((1, 2, 8000, 0, 'NONE', 'not compressed'))
        out.writeframes(b''.join(struct.pack('<h', int(1000 * math.sin(i * 0.1))) for i in range(2400)))
    return str(target)


def evidence(audio, kind):
    return {'schema': 1, 'master_sha256': inspect_audio(audio)['sha256'],
            'kind': kind, 'engine': 'contract_fixture_NOT_real_model', 'revision': 'test1',
            'checks': dict.fromkeys(CHECKS[kind], True), 'vocal_method': 'singing'}


def test_high_score_lyrics_and_rvc_flags_do_not_prove_song(audio):
    result = assess_result({'master_path': audio, 'hit_score': 100,
                            'lyrics': {'ok': True}, 'voice': {'ok': True, 'source': 'rvc'}})
    assert result['status'] == 'degraded'
    assert result['kind'] == 'unverified_audio'
    assert not result['succeeded']
    assert not result['quality_accepted']


@pytest.mark.parametrize('kind', list(CHECKS))
def test_matching_provenance_can_satisfy_typed_contract_not_quality(audio, kind):
    result = assess_result({'master_path': audio, 'render_evidence': evidence(audio, kind), 'requested_kind': kind})
    assert result['succeeded']
    assert result['kind'] == kind
    assert not result['quality_accepted']


@pytest.mark.parametrize('method', ['tts', 'silero', 'xtts', 'rvc', None])
def test_tts_or_rvc_cannot_certify_generated_singing(audio, method):
    proof = evidence(audio, 'generated_singing'); proof['vocal_method'] = method
    assert not assess_result({'master_path': audio, 'render_evidence': proof})['succeeded']


def test_changed_audio_hash_invalidates_stale_provenance(audio):
    proof = evidence(audio, 'generated_singing'); proof['master_sha256'] = '0' * 64
    assert assess_result({'master_path': audio, 'render_evidence': proof})['status'] == 'degraded'


def test_speech_never_satisfies_singing_request(audio):
    result = assess_result({'master_path': audio, 'render_evidence': evidence(audio, 'speech_draft')})
    assert result['kind'] == 'speech_draft' and not result['succeeded']


@pytest.mark.parametrize('extra', [{'blocked': [{'stage': 'voice'}]}, {'canceled': True}])
def test_blocked_or_canceled_run_is_never_complete(audio, extra):
    result = assess_result({'master_path': audio, 'render_evidence': evidence(audio, 'generated_singing'), **extra})
    assert not result['succeeded']


@pytest.mark.parametrize('payload', [{}, {'master_path': 'not-there.wav'}, {'master_path': ''}])
def test_missing_artifact_is_failed(payload):
    assert assess_result(payload)['status'] == 'failed'


def test_silence_and_corrupt_wav_fail(tmp_path):
    target = tmp_path / 'silent.wav'
    with wave.open(str(target), 'wb') as out:
        out.setparams((1, 2, 8000, 0, 'NONE', 'not compressed')); out.writeframes(bytes(8000))
    assert not inspect_audio(str(target))['valid']
    target.write_bytes(b'not audio')
    assert not inspect_audio(str(target))['valid']


def test_bad_provenance_is_degraded_not_a_crash(audio):
    for bad in ['bad', [], {'kind': 'generated_singing', 'checks': 'yes'}]:
        assert not assess_result({'master_path': audio, 'render_evidence': bad, 'hit': 'bad'})['succeeded']


def test_agent_cli_nonzero_when_only_a_master_exists(audio, monkeypatch):
    from types import SimpleNamespace
    from app.cli import agent_task
    import modules.agent_guide as guide

    monkeypatch.setattr(agent_task, '_prepare', lambda *_: {})
    monkeypatch.setattr(guide, 'run_conversation_hit', lambda *a, **kw: {'master_path': audio})
    args = SimpleNamespace(online=False)
    assert agent_task.run_agent_hit(args) == 1


def test_unhashable_kind_is_rejected_not_a_crash(audio):
    result = assess_result({'master_path': audio, 'render_evidence': {'kind': []}})
    assert not result['succeeded']


def test_nonfinite_and_out_of_range_audio_is_rejected(tmp_path):
    import numpy as np
    import soundfile as sf
    target = tmp_path / 'bad.wav'
    for value in (np.nan, np.inf, 2.0):
        sf.write(target, np.full(2000, value, dtype='float32'), 8000, subtype='FLOAT')
        assert not inspect_audio(str(target))['valid']

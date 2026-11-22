"""Canonical outcome is distinct from backwards-compatible stage accounting."""
import pytest

from app.pipeline import StageResult, StageStatus, classify, summarize
from app.pipeline.outcome import stage_outcome


@pytest.mark.parametrize('state,expected', [('OK', 'success'), ('FALLBACK', 'degraded'),
    ('BLOCKED', 'blocked'), ('FAILED', 'failed'), ('CANCELED', 'canceled'), ('MAGIC', 'failed')])
def test_explicit_stage_status_overrides_misleading_ok_flag(state, expected):
    result = stage_outcome([{'name': 'music', 'status': state, 'ok': True}])
    assert result['status'] == expected
    assert result['succeeded'] == (state == 'OK')
    assert not result['song_verified']


def test_optional_blocker_degrades_instead_of_blocking_required_output():
    result = stage_outcome([{'name': 'music', 'status': 'OK'},
                            {'name': 'cover', 'status': 'FAILED', 'required': False, 'reason': 'offline'}])
    assert result['status'] == 'degraded'
    assert 'offline' in result['reasons'][0]


def test_empty_run_does_not_succeed():
    assert not stage_outcome([])['succeeded']
    assert summarize([])['outcome']['status'] == 'blocked'


def test_cancellation_serializes_and_does_not_count_as_success():
    stage = classify({'canceled': True}, name='voice')
    assert stage.status is StageStatus.CANCELED and not stage.ok
    assert not stage.succeeded
    assert stage.to_dict()['required']
    assert summarize([stage])['outcome']['status'] == 'canceled'


def test_required_blocker_overrides_legacy_percent():
    stages = [StageResult('music', StageStatus.OK), StageResult('voice', StageStatus.BLOCKED, reason='no weights')]
    summary = summarize(stages)
    assert summary['outcome']['status'] == 'blocked'
    assert not summary['outcome']['succeeded']
    assert summary['percent_kind'] == 'legacy_stage_accounting_not_product_readiness'


def test_successful_placeholder_cannot_give_canonical_success():
    assert stage_outcome([{'name': 'vocal', 'status': 'OK', 'output': {'placeholder': True}}])['status'] == 'degraded'


def test_missing_required_stage_is_explicitly_blocked():
    result = stage_outcome([{'name': 'music', 'status': 'OK'}], required_names=['music', 'voice'])
    assert result['status'] == 'blocked'
    assert 'voice' in result['reasons'][0]


@pytest.mark.parametrize('kwargs', [{'quality_failures': ['bad peak']}, {'dry_run': True}, {'only': ['beat']}])
def test_qa_failure_or_partial_run_never_gives_complete_success(kwargs):
    from app.pipeline.outcome import report_outcome
    assert not report_outcome([{'name': 'music', 'status': 'OK'}], **kwargs)['succeeded']

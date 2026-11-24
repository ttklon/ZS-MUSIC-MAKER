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


def test_baseline_legacy_blocked_fields_are_pass_like_but_canonical_outcome_blocks():
    blocked = StageResult('voice', StageStatus.BLOCKED, reason='model missing')
    summary = summarize([blocked])
    assert blocked.ok is True  # compatibility projection: not failed/canceled
    assert blocked.succeeded is False
    assert summary['verdict'] == 'PASS_BLOCKED'  # legacy display field
    assert summary['outcome']['status'] == 'blocked'
    assert summary['outcome']['succeeded'] is False


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


@pytest.mark.parametrize('dry_run', [False, True])
def test_empty_legacy_summary_never_claims_pass(dry_run):
    summary = summarize([], dry_run=dry_run)
    assert summary['verdict'] == 'BLOCKED'
    assert summary['percent'] == 0
    assert not summary['outcome']['succeeded']


@pytest.mark.parametrize('state', ['FAILED', 'CANCELED', 'UNKNOWN'])
def test_misleading_legacy_ok_cannot_override_failure(state):
    summary = summarize([{'name': 'voice', 'status': state, 'ok': True}])
    assert summary['verdict'] == 'PARTIAL'
    assert summary['percent'] == 0
    assert not summary['outcome']['succeeded']


def test_executor_cannot_downgrade_caller_required_stage():
    result = stage_outcome([{'name': 'music', 'status': 'BLOCKED', 'required': False},
                            {'name': 'mix', 'status': 'OK'}], required_names=['music', 'mix'])
    assert result['status'] == 'blocked'
    assert result['stages'][0]['required'] is True


@pytest.mark.parametrize('bad', [None, 7, {'name': []}, {'name': 'voice', 'status': []},
    {'name': 'voice', 'status': 'OK', 'ok': False}, {'name': 'voice', 'status': 'OK', 'required': 'false'}])
def test_malformed_stage_fails_closed_without_crashing(bad):
    assert stage_outcome([bad])['status'] == 'failed'


def test_duplicate_stage_cannot_hide_conflicting_output():
    result = stage_outcome([{'name': 'voice', 'status': 'OK'},
                            {'name': 'voice', 'status': 'BLOCKED', 'required': False}])
    assert result['status'] == 'failed'


@pytest.mark.parametrize('kwargs', [
    {'required_names': 'voice'},
    {'required_names': ['voice', '']},
    {'required_names': ['voice', []]},
    {'not_requested_names': None},
    {'not_requested_names': {'voice': True}},
    {'not_requested_names': 3},
])
def test_malformed_stage_name_contract_fails_closed(kwargs):
    result = stage_outcome([{'name': 'music', 'status': 'OK'}], **kwargs)
    assert result['status'] == 'failed'
    assert not result['succeeded']
    assert result['reasons']


def test_malformed_stage_collection_fails_closed():
    result = stage_outcome(None)
    assert result['status'] == 'failed'
    assert not result['succeeded']


def test_report_propagates_required_stage_contract():
    from app.pipeline.outcome import report_outcome
    assert report_outcome([{'name': 'mix', 'status': 'OK'}], required_names=['mix', 'voice'])['status'] == 'blocked'


@pytest.mark.parametrize('row', [{'name': 'voice', 'ok': True},
    {'name': 'voice', 'status': 'OK', 'ok': False}])
def test_legacy_and_canonical_summary_both_reject_incomplete_or_conflicting_status(row):
    result = summarize([row])
    assert result['verdict'] == 'PARTIAL'
    assert not result['outcome']['succeeded']


def test_adapter_preserves_stricter_producer_outcome_and_quality_gate():
    from app.pipeline.outcome import outcome_from_report
    report = {'stages': [{'name': 'mix', 'status': 'OK'}],
              'outcome': {'status': 'blocked', 'reasons': ['required voice absent']}}
    assert outcome_from_report(report)['status'] == 'blocked'
    report['quality_gate_failures'] = ['bad peak']
    assert outcome_from_report(report)['status'] == 'failed'


def test_adapter_rejects_contradictory_declared_canonical_success():
    from app.pipeline.outcome import outcome_from_report
    result = outcome_from_report({'stages': [{'name': 'mix', 'status': 'OK'}],
                                  'outcome': {'status': 'success', 'succeeded': False}})
    assert result['status'] == 'failed'


@pytest.mark.parametrize('reasons', ['bad-shape', 7, ['valid', 3], None])
def test_adapter_malformed_declared_reasons_fail_closed(reasons):
    from app.pipeline.outcome import outcome_from_report
    result = outcome_from_report({'stages': [{'name': 'mix', 'status': 'OK'}],
                                  'outcome': {'status': 'blocked', 'reasons': reasons}})
    assert result['status'] == 'failed'
    assert not result['succeeded']


def test_canceled_retry_does_not_mutate_previous_successful_records():
    prior_stages = [{'name': 'music', 'status': 'OK'}]
    prior_snapshot = [dict(row) for row in prior_stages]
    prior = stage_outcome(prior_stages, required_names=['music'])
    retry = stage_outcome([{'name': 'music', 'status': 'CANCELED', 'reason': 'user stopped'}],
                          required_names=['music', 'voice'])
    assert prior['status'] == 'success' and prior['succeeded'] is True
    assert prior_stages == prior_snapshot
    assert retry['status'] == 'canceled' and retry['succeeded'] is False
    assert any('user stopped' in reason for reason in retry['reasons'])


def test_only_caller_can_authorize_not_requested_blocked_stages():
    stages = [{'name': 'mix', 'status': 'OK'}, {'name': 'voice', 'status': 'BLOCKED',
               'output': {'requested': False, 'skip_kind': 'user_disabled'}}]
    assert stage_outcome(stages)['status'] == 'blocked'
    result = stage_outcome(stages, required_names=['mix'], not_requested_names=['voice'])
    assert result['succeeded'] is True
    assert result['stages'][1]['status'] == 'not_requested'
    assert not stage_outcome(stages, required_names=['mix', 'voice'], not_requested_names=['voice'])['succeeded']
    for status in ('FAILED', 'CANCELED', 'UNKNOWN', 'FALLBACK'):
        stages[1]['status'] = status
        assert not stage_outcome(stages, required_names=['mix'], not_requested_names=['voice'])['succeeded']


def test_untrusted_adapter_does_not_infer_skip_permission_from_producer_scope():
    from app.pipeline.outcome import outcome_from_report
    report = {'stages': [{'name': 'mix', 'status': 'OK'}, {'name': 'voice', 'status': 'BLOCKED'}],
              'request_scope': {'not_requested': ['voice']}, 'outcome': {'status': 'success', 'succeeded': True}}
    assert outcome_from_report(report)['status'] == 'blocked'

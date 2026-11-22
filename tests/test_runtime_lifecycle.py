"""Preparation, stage activity and correlated logs; not real model/inference acceptance."""
import json
import logging
import time

import pytest

from app.core.bootstrap_report import summarize_setup


def test_empty_or_missing_model_inventory_cannot_become_ready():
    for value in ({}, {'heavy': {}, 'models': {}, 'ollama': {'ok': True}}):
        result = summarize_setup(value)
        assert result['schema'] == 1
        assert result['ok'] is False
        assert result['inference_verified'] is False


def test_bootstrap_emits_typed_blocked_terminal(monkeypatch, capsys):
    from app.cli import commands
    from app.core import bootstrap
    from app.core import net_policy
    monkeypatch.setattr(bootstrap, 'wire_full_agents', lambda: None)
    monkeypatch.setattr(bootstrap, 'auto_bootstrap', lambda **kw: {'ok': True})
    monkeypatch.setattr(net_policy, 'network_allowed', lambda: False)
    monkeypatch.setenv('ZSMM_TASK_ID', 'bootstrap-test')
    assert commands.run_bootstrap() == 1
    events = []
    for line in capsys.readouterr().out.splitlines():
        try:
            data = json.loads(line)
        except ValueError:
            continue
        if data.get('schema') == 'zsmm.task':
            events.append(data)
    assert events[-1]['type'] == 'done'
    assert events[-1]['ok'] is False
    assert events[-1]['report']['setup']['ok'] is False
    assert events[-1]['task_id'] == 'bootstrap-test'


def test_stage_heartbeat_does_not_interrupt_slow_cpu_and_stops_on_exit(caplog):
    from app.ai.activity import stage_activity
    with caplog.at_level(logging.INFO, logger='SequentialAIRunner'):
        with stage_activity('cpu-fixture', interval_sec=0.01):
            time.sleep(0.05)
        count = len(caplog.records)
        time.sleep(0.03)
    assert count > 0 and len(caplog.records) == count
    assert all('not measured model progress' in r.message for r in caplog.records)


def test_logger_adds_validated_task_id_and_still_redacts(monkeypatch):
    from app.core.logger import _SecretRedactingFilter
    monkeypatch.setenv('ZSMM_TASK_ID', 'task-123')
    record = logging.LogRecord('test', logging.ERROR, '', 1, 'token=verysecret', (), None)
    assert _SecretRedactingFilter().filter(record)
    assert record.task_id == 'task-123'
    assert 'verysecret' not in record.getMessage()
    monkeypatch.setenv('ZSMM_TASK_ID', 'bad\nINJECT')
    _SecretRedactingFilter().filter(record)
    assert record.task_id == 'none'


def test_installed_workspace_logger_does_not_fallback_to_install_tree(monkeypatch, tmp_path):
    from app.core.logger import _candidate_dirs
    monkeypatch.setenv('ZSMM_WORKSPACE', str(tmp_path))
    assert not any(str(p).endswith('output/logs') for p in _candidate_dirs())


def test_exception_traceback_is_redacted_after_formatting():
    from app.core.logger import _RedactingFormatter, _SecretRedactingFilter
    import sys
    try:
        raise RuntimeError('password="private words" token=privatetoken')
    except RuntimeError:
        record = logging.LogRecord('test', logging.ERROR, '', 1, 'failed', (), sys.exc_info())
    _SecretRedactingFilter().filter(record)
    formatted = _RedactingFormatter('%(task_id)s %(message)s').format(record)
    assert 'private words' not in formatted
    assert 'privatetoken' not in formatted
    assert 'RuntimeError' in formatted

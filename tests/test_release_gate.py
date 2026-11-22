"""Publication contracts, not real song/installer acceptance."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.release_gate import GATES, ROOT, evaluate, validate_blockers

COMMIT = 'a' * 40


def registry():
    return json.loads((ROOT / 'docs/release/blockers.json').read_text(encoding='utf-8'))


def approved_fixture(tmp_path):
    # Synthetic gate tests deliberately do not update product acceptance.json.
    file = tmp_path / 'measurement.txt'
    file.write_text('synthetic measured bytes')
    evidence = {'path': file.name, 'sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
                'kind': 'measured'}
    gates = {key: {'accepted': True, 'reviewer': 'test-only', 'evidence': [evidence]}
             for key in GATES}
    blockers = registry()
    for row in blockers['blockers']:
        row['status'] = 'resolved'
        row['resolution_evidence'] = [evidence]
    return {'schema_version': 1, 'source_commit': COMMIT, 'gates': gates}, blockers


def test_real_registry_has_reproduction_scenario_and_regression():
    data = registry()
    validate_blockers(data)
    assert {r['priority'] for r in data['blockers']} == {'P0', 'P1'}
    assert data['blockers'][0]['id'] == 'F01'
    assert data['blockers'][0]['status'] == 'open'


def test_actual_publication_is_blocked_not_readiness_score():
    result = subprocess.run([sys.executable, 'tools/release_gate.py'], cwd=ROOT,
                            capture_output=True, text=True)
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report['publication_allowed'] is False
    assert any('F01' in r for r in report['reasons'])
    assert any('G4' in r for r in report['reasons'])


def test_positive_fixture_is_hash_and_commit_bound(tmp_path):
    acceptance, blockers = approved_fixture(tmp_path)
    assert evaluate(acceptance, blockers, tmp_path, COMMIT)['publication_allowed']
    assert not evaluate(acceptance, blockers, tmp_path, 'b' * 40)['publication_allowed']
    (tmp_path / 'measurement.txt').write_text('tampered')
    assert not evaluate(acceptance, blockers, tmp_path, COMMIT)['publication_allowed']


@pytest.mark.parametrize('key', GATES)
def test_every_gate_is_mandatory(tmp_path, key):
    acceptance, blockers = approved_fixture(tmp_path)
    del acceptance['gates'][key]
    assert not evaluate(acceptance, blockers, tmp_path, COMMIT)['publication_allowed']


@pytest.mark.parametrize('change', [
    {'path': '../outside.txt'}, {'path': '/absolute.txt'}, {'path': 'absent.txt'},
    {'kind': 'fixture'}, {'sha256': '0' * 64},
])
def test_untrusted_evidence_never_passes(tmp_path, change):
    acceptance, blockers = approved_fixture(tmp_path)
    acceptance['gates']['G1']['evidence'][0].update(change)
    assert not evaluate(acceptance, blockers, tmp_path, COMMIT)['publication_allowed']


def test_open_mandatory_blocker_overrides_green_gates(tmp_path):
    acceptance, blockers = approved_fixture(tmp_path)
    blockers['blockers'][0]['status'] = 'open'
    assert not evaluate(acceptance, blockers, tmp_path, COMMIT)['publication_allowed']


@pytest.mark.parametrize('mutation', ['duplicate', 'cycle', 'no_evidence', 'no_regression'])
def test_registry_corruption_is_rejected(mutation):
    data = copy.deepcopy(registry())
    row = data['blockers'][0]
    if mutation == 'duplicate':
        data['blockers'].append(copy.deepcopy(row))
    elif mutation == 'cycle':
        row['depends_on'] = ['F09']
    elif mutation == 'no_evidence':
        row['status'] = 'resolved'
    else:
        row['regression'] = ''
    with pytest.raises(AssertionError):
        validate_blockers(data)


@pytest.mark.parametrize('workflow', ['build', 'release'])
def test_all_publication_workflows_are_gated_and_non_destructive(workflow):
    text = (ROOT / f'.github/workflows/{workflow}.yml').read_text(encoding='utf-8')
    publish = text[text.index('  publish-release:'):]
    assert publish.index('tools/release_gate.py') < publish.index('softprops/action-gh-release')
    assert 'delete-asset' not in publish
    assert 'concurrency: product-release-publication' in publish
    assert 'gh api --paginate' in publish
    sections = publish.split('uses: softprops/action-gh-release@v2')[1:]
    assert sections
    for section in sections:
        assert 'overwrite_files: false' in section


def test_resolved_blocker_with_missing_proof_stays_blocked(tmp_path):
    acceptance, blockers = approved_fixture(tmp_path)
    blockers['blockers'][0]['resolution_evidence'] = [
        {'path': 'missing.txt', 'sha256': '0' * 64, 'kind': 'measured'}]
    assert not evaluate(acceptance, blockers, tmp_path, COMMIT)['publication_allowed']


@pytest.mark.parametrize('content', ['{}', '[]', 'null', '{bad json'])
def test_malformed_input_cli_fails_closed(tmp_path, content):
    base = tmp_path / 'docs/release'
    base.mkdir(parents=True)
    (base / 'acceptance.json').write_text(content)
    (base / 'blockers.json').write_text(content)
    result = subprocess.run([sys.executable, str(ROOT / 'tools/release_gate.py'),
                             '--root', str(tmp_path), '--commit', COMMIT],
                            capture_output=True, text=True)
    assert result.returncode == 1
    assert json.loads(result.stdout)['publication_allowed'] is False

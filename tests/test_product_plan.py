"""Planning integrity only: these tests do not certify product readiness."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools.build_product_plan import ROOT, validate, workpackages

BASE = ROOT / 'docs' / 'plan'


def load_plan():
    return json.loads((BASE / 'backlog.json').read_text(encoding='utf-8'))


def test_exactly_1000_tasks_with_valid_paths_and_dependencies():
    data = load_plan()
    validate(data)
    assert len({p['group'] for p in data['packages']}) == 10
    for number in range(1, 101):
        assert sum(t['package'] == number for t in data['tasks']) == 10


def test_readable_plan_contains_every_task_once():
    text = (BASE / 'PLAN_1000.md').read_text(encoding='utf-8')
    headings = [line.split('.')[0].removeprefix('### ') for line in text.splitlines() if line.startswith('### T')]
    assert headings == [f'T{n:04}' for n in range(1, 1001)]


def test_plan_never_closes_task_without_evidence():
    data = copy.deepcopy(load_plan())
    data['tasks'][0]['status'] = 'verified'
    data['tasks'][0]['evidence'] = []
    with pytest.raises(AssertionError, match='Missing evidence'):
        validate(data)


def test_circular_or_forward_dependency_is_rejected():
    data = copy.deepcopy(load_plan())
    data['tasks'][0]['depends_on'] = ['T1000']
    with pytest.raises(AssertionError):
        validate(data)


def test_domain_specification_matches_package_identity():
    data = load_plan()
    for actual, source in zip(data['packages'], workpackages(), strict=True):
        for key in ('number', 'group', 'title', 'paths', 'target', 'acceptance', 'failure'):
            assert actual[key] == source[key]


def test_inventory_describes_original_baseline_not_runtime_certification():
    inventory = json.loads((BASE / 'repository-inventory.json').read_text(encoding='utf-8'))
    assert inventory['baseline_commit'] == load_plan()['baseline_commit']
    assert inventory['totals']['files'] == len(inventory['files'])
    assert len({f['path'] for f in inventory['files']}) == inventory['totals']['files']
    assert all(len(f['sha256']) == 64 for f in inventory['files'])
    assert 'Not semantic review or runtime proof' in inventory['scope']


def test_all_responsibility_paths_are_tracked_not_local_runtime_folders():
    import subprocess

    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    for package in load_plan()['packages']:
        for path in package['paths']:
            assert any(f == path or f.startswith(path + '/') for f in tracked), path

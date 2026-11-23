"""Queue integrity is not execution or product acceptance."""
import copy
import json
from pathlib import Path

import pytest

from tools.check_plan_restart import validate_restart

BASE = Path(__file__).resolve().parents[1] / 'docs/plan'


def load():
    return (json.loads((BASE / 'restart.json').read_text(encoding='utf-8')),
            json.loads((BASE / 'backlog.json').read_text(encoding='utf-8')))


def test_restart_covers_all_1000_and_starts_at_first_fifty():
    data, backlog = load()
    result = validate_restart(data, backlog)
    assert (result['active_first'], result['active_last']) == ('T0001', 'T0050')
    assert not result['product_acceptance_verified_by_this_tool']


@pytest.mark.parametrize('mutation', ['omit', 'duplicate', 'reorder', 'unearned'])
def test_invalid_restart_is_rejected(mutation):
    data, backlog = load()
    data = copy.deepcopy(data)
    if mutation == 'omit': data['batches'][0].pop()
    if mutation == 'duplicate': data['batches'][0][1] = 'T0001'
    if mutation == 'reorder': data['batches'][0].reverse()
    if mutation == 'unearned': data['reviews'][0]['state'] = 'complete'
    with pytest.raises(AssertionError):
        validate_restart(data, backlog)


def test_cannot_jump_past_unfinished_batch():
    data, backlog = load()
    data['current_batch'] = 1
    data['reviews'] += [dict(data['reviews'][0], id=task) for task in data['batches'][1]]
    with pytest.raises(AssertionError, match='Cannot skip'):
        validate_restart(data, backlog)

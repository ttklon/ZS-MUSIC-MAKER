"""Validate restart coverage and prohibit skipping unfinished ten-task batches."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/plan'


def validate_restart(data, backlog):
    expected = [t['id'] for t in backlog['tasks']]
    assert data['schema'] == 1 and data['batch_size'] == 10
    assert [task for batch in data['batches'] for task in batch] == expected, 'Missing, duplicate or reordered task'
    assert all(len(batch) == 10 for batch in data['batches'])
    current = data['current_batch']
    assert type(current) is int and 0 <= current < len(data['batches'])
    reviewed = data.get('reviewed_through_batch', current)
    assert type(reviewed) is int and current <= reviewed < len(data['batches'])
    records = data['reviews']
    assert [r['id'] for r in records] == [task for batch in data['batches'][:reviewed + 1] for task in batch]
    for row in records:
        assert row['state'] in ('in_progress', 'complete')
        assert row['evidence'] and all((ROOT / path).is_file() for path in row['evidence'])
        if row['state'] == 'complete':
            assert row['acceptance_met'] is True, 'No acceptance for completed task'
            assert row['remaining'] == []
        else:
            assert row['acceptance_met'] is False
    prior = set(task for batch in data['batches'][:current] for task in batch)
    assert all(r['state'] == 'complete' for r in records if r['id'] in prior), 'Cannot skip unfinished batch'
    return {'queue_valid': True, 'total': len(expected), 'active_first': data['batches'][current][0],
            'active_last': data['batches'][current][-1],
            'complete_in_new_pass': sum(r['state'] == 'complete' for r in records),
            'product_acceptance_verified_by_this_tool': False}


def main():
    data = json.loads((BASE / 'restart.json').read_text(encoding='utf-8'))
    backlog = json.loads((BASE / 'backlog.json').read_text(encoding='utf-8'))
    print(json.dumps(validate_restart(data, backlog)))


if __name__ == '__main__':
    main()

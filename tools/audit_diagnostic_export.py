"""Independent stdlib export-schema consumer. Does not trust producer redaction."""
import argparse
import json
from pathlib import Path

SOURCES = {'task', 'python', 'python-launch', 'renderer', 'startup', 'preload', 'load'}
EVENTS = {'start', 'stopping', 'timeout', 'exit', 'error', 'protocol-error', 'cleanup-failed', 'done'}


def audit(data):
    assert set(data) == {'schema', 'privacy', 'entries'}
    assert data['schema'] == 2 and data['privacy'] == 'structured-only-no-free-text'
    assert isinstance(data['entries'], list) and len(data['entries']) <= 5000
    for row in data['entries']:
        assert set(row) <= {'source', 'task', 'event', 'code', 'ok', 'canceled', 'timedOut', 'cleanupConfirmed'}
        assert row['source'] in SOURCES
        assert row['task'] is None or (type(row['task']) is int and 0 < row['task'] <= 5000)
        if 'event' in row:
            assert row['event'] in EVENTS
        if 'code' in row:
            assert type(row['code']) is int and abs(row['code']) <= 4294967295
        for key in ('ok', 'canceled', 'timedOut', 'cleanupConfirmed'):
            if key in row:
                assert type(row[key]) is bool
    return {'ok': True, 'entries': len(data['entries']), 'free_text_fields': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(json.loads(args.file.read_text(encoding='utf-8-sig')))))


if __name__ == '__main__':
    main()

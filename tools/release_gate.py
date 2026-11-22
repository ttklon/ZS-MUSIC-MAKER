"""Fail-closed publication gate; evidence integrity is not human/audio acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATES = {
    'G0': 'scope_and_scenarios', 'G1': 'clean_windows_nsis',
    'G2': 'models_recovery_offline', 'G3': 'real_instrumental',
    'G4': 'own_and_automatic_singing', 'G5': 'revision_history',
    'G6': 'audio_metrics_and_human_listening', 'G7': 'ten_short_three_full_failure_matrix',
    'G8': 'update_and_publisher', 'G9': 'no_mandatory_p0_p1',
}


def validate_blockers(data: dict) -> None:
    assert data['schema_version'] == 1
    rows = data['blockers']
    ids = {r['id'] for r in rows}
    assert rows and len(ids) == len(rows), 'Empty/duplicate blocker registry'
    for row in rows:
        assert type(row['mandatory']) is bool
        assert row['priority'] in ('P0', 'P1')
        assert row['status'] in ('open', 'resolved')
        for field in ('scenario', 'reproduce', 'expected', 'observed', 'regression', 'owner'):
            assert isinstance(row[field], str) and row[field].strip(), field
        assert set(row['gates']) <= GATES.keys() and row['gates']
        assert set(row['depends_on']) <= ids and row['id'] not in row['depends_on']
        if row['status'] == 'resolved':
            assert row.get('resolution_evidence'), 'Resolution requires evidence'
    def visit(key, trail):
        assert key not in trail, 'Cyclic blocker dependencies'
        row = next(r for r in rows if r['id'] == key)
        for dep in row['depends_on']:
            visit(dep, trail | {key})
    for key in ids:
        visit(key, set())


def evidence_error(item: dict, root: Path) -> str | None:
    relative = Path(item.get('path', ''))
    if relative.is_absolute() or '..' in relative.parts or not relative.parts:
        return 'unsafe evidence path'
    file = (root / relative).resolve()
    if not file.is_relative_to(root.resolve()) or not file.is_file():
        return 'missing evidence file'
    digest = hashlib.sha256(file.read_bytes()).hexdigest()
    if digest != item.get('sha256'):
        return 'evidence hash mismatch'
    if item.get('kind') not in ('measured', 'human_review'):
        return 'fixtures and declarations are not acceptance evidence'
    return None


def evaluate(acceptance: dict, blockers: dict, root: Path, commit: str) -> dict:
    validate_blockers(blockers)
    reasons = []
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        reasons.append('invalid expected source commit')
    if acceptance.get('schema_version') != 1 or acceptance.get('source_commit') != commit:
        reasons.append('acceptance missing or for another commit')
    for row in blockers['blockers']:
        if row['mandatory'] and row['status'] != 'resolved':
            reasons.append(f"open {row['priority']} {row['id']}: {row['scenario']}")
        if row['status'] == 'resolved':
            for item in row['resolution_evidence']:
                error = evidence_error(item, root)
                if error:
                    reasons.append(f"{row['id']}: {error}")
    for key, title in GATES.items():
        gate = acceptance.get('gates', {}).get(key, {})
        if gate.get('accepted') is not True or not gate.get('reviewer') or not gate.get('evidence'):
            reasons.append(f'{key} {title}: acceptance/reviewer/evidence missing')
            continue
        for item in gate['evidence']:
            error = evidence_error(item, root)
            if error:
                reasons.append(f'{key}: {error}')
    return {'publication_allowed': not reasons, 'source_commit': commit, 'reasons': reasons,
            'limitation': 'Hash binding is not independent listening or a trusted signature.'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--commit')
    args = parser.parse_args()
    try:
        commit = args.commit or subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=args.root, text=True).strip()
        base = args.root / 'docs' / 'release'
        result = evaluate(json.loads((base / 'acceptance.json').read_text(encoding='utf-8')),
                          json.loads((base / 'blockers.json').read_text(encoding='utf-8')),
                          args.root, commit)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, AssertionError) as exc:
        result = {'publication_allowed': False, 'reasons': [f'Invalid gate inputs: {exc}']}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['publication_allowed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

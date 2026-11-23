"""Separate Python consumer checks JS exports, including unseen secrets."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from tools.audit_diagnostic_export import audit


def test_js_producer_is_accepted_without_private_free_text():
    if not shutil.which('node'):
        pytest.skip('node required for cross-language producer check')
    root = Path(__file__).resolve().parents[1]
    script = r'''
const {safeExport} = require('./desktop/electron/diagnostic-export');
const secret = require('node:crypto').randomBytes(32).toString('hex');
const lines = [
  {source:'renderer', taskId:secret, message:secret},
  {source:'python', taskId:secret, message:'private lyric '+secret},
  {source:'task', taskId:secret, message:JSON.stringify({type:'exit', code:2, ok:false, key:secret})},
  {source:secret, message:secret},
];
const out = safeExport(lines.map(x=>JSON.stringify(x)).join('\n'));
if (JSON.stringify(out).includes(secret)) throw Error('private canary exported');
console.log(JSON.stringify(out));
'''
    completed = subprocess.run(['node', '-e', script], cwd=root, text=True,
                               capture_output=True, timeout=15, check=True)
    result = audit(json.loads(completed.stdout))
    assert result == {'ok': True, 'entries': 3, 'free_text_fields': 0}


@pytest.mark.parametrize('field,value', [
    ('message', 'private'), ('path', 'C:\\Users\\someone'),
    ('task', 'private-project'), ('event', 'private lyric'),
    ('code', 'private token'), ('ok', 'private'), ('source', 'private'),
])
def test_consumer_rejects_unapproved_fields_and_types(field, value):
    data = {'schema': 2, 'privacy': 'structured-only-no-free-text',
            'entries': [{'source': 'task', 'task': 1, field: value}]}
    with pytest.raises(AssertionError):
        audit(data)

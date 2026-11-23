"""Bounded probe handshake; does not load models into the UI/application runtime."""
from __future__ import annotations

import json
import subprocess
import uuid
from pathlib import Path

from app.ai.engine_profiles import profile


def probe_worker(executable: Path, name: str, timeout_sec: float = 10) -> dict:
    data = profile(name)
    nonce = uuid.uuid4().hex
    command = [str(executable), '-I', str(Path(__file__).with_name('worker_entry.py')),
               '--profile', name, '--fingerprint', data['input_sha256']]
    try:
        completed = subprocess.run(command, input=json.dumps(dict(version=1, operation='probe', nonce=nonce)) + '\n',
                                   text=True, capture_output=True, timeout=timeout_sec)
        if completed.returncode or len(completed.stdout) > 65536:
            raise ValueError('worker exit/output limit invalid')
        records = [json.loads(line) for line in completed.stdout.splitlines()]
        if len(records) != 2 or [r.get('type') for r in records] != ['hello', 'result']:
            raise ValueError('missing or ambiguous handshake')
        for row in records:
            if (row.get('schema'), row.get('version'), row.get('profile'), row.get('fingerprint')) != (
                    'zsmm.worker', 1, name, data['input_sha256']):
                raise ValueError('worker version/profile fingerprint mismatch')
        result = records[-1]
        if result.get('nonce') != nonce or result.get('isolated') is not True:
            raise ValueError('worker correlation/isolation mismatch')
        if result.get('python_version') != [3, 11] or result.get('artifacts') != [] or result.get('ok') is not True:
            raise ValueError('worker interpreter/result mismatch')
        if name != 'core' and result.get('venv') is not True:
            raise ValueError('engine profile requires its own virtual environment')
        return result
    except (OSError, ValueError, TypeError, subprocess.TimeoutExpired) as exc:
        return dict(ok=False, profile=name, inference_verified=False, reason=str(exc))

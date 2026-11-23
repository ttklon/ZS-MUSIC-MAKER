"""Stdlib-only isolated worker v1. Probe only; no model/ad-hoc code execution."""
import argparse
import json
import re
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', required=True)
    parser.add_argument('--fingerprint', required=True)
    args = parser.parse_args()
    def emit(kind, **payload):
        print(json.dumps(dict(schema='zsmm.worker', version=1, type=kind,
                              profile=args.profile, fingerprint=args.fingerprint, **payload)), flush=True)
    emit('hello')
    try:
        raw = sys.stdin.buffer.readline(65537)
        if len(raw) > 65536:
            raise ValueError('request too large')
        request = json.loads(raw)
        if set(request) != {'version', 'operation', 'nonce'} or request['version'] != 1:
            raise ValueError('unsupported worker request')
        if request['operation'] != 'probe' or not re.fullmatch(r'[a-f0-9]{32}', request['nonce']):
            raise ValueError('only a correlated probe is supported; model adapters are not accepted')
        emit('result', nonce=request['nonce'], ok=True, artifacts=[],
             python_version=list(sys.version_info[:2]), executable=sys.executable,
             isolated=sys.flags.isolated == 1, venv=sys.prefix != sys.base_prefix,
             inference_verified=False)
        return 0
    except (ValueError, KeyError, TypeError) as exc:
        emit('error', ok=False, message=str(exc))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

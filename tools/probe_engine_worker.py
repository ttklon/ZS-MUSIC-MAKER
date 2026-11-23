"""Read-only subprocess protocol probe; no weights, install or inference."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.ai.worker_client import probe_worker
from app.ai.engine_profiles import PROFILES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=PROFILES, default='core')
    parser.add_argument('--python', default=sys.executable)
    args = parser.parse_args()
    result = probe_worker(Path(args.python), args.profile)
    print(json.dumps(result, ensure_ascii=True))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

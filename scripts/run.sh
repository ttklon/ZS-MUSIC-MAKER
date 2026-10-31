#!/usr/bin/env bash
# ZS Music Maker — POSIX launcher (dev/CI helper; target platform is Windows 11)
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=python3; fi
exec "$PY" main.py "$@"

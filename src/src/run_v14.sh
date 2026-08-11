#!/bin/bash
# ZS Music Maker v14 — launcher
cd "$(dirname "$0")"
PYTHONPATH=. python3 main.py "$@"

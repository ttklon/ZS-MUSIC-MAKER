#!/usr/bin/env bash
set -e

echo "=================================================="
echo "ZS-MUSIC-MAKER PROFESSIONAL QUALITY GATE"
echo "Enforcing Claude Code / Genspark strict standards"
echo "=================================================="

cd "$(dirname "$0")/.."

echo "[1/3] Running Pytest unit tests..."
python3 -m pytest tests/

echo "[2/3] Running Mypy type checking..."
mypy --ignore-missing-imports modules/pro_audio_dsp.py tests/test_pro_audio_dsp.py

echo "[3/3] Running Pylint code quality check..."
pylint modules/pro_audio_dsp.py tests/test_pro_audio_dsp.py

echo "=================================================="
echo "QUALITY GATE PASSED WITH 10/10 SCORE! 🚀"
echo "=================================================="

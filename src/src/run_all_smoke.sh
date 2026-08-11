#!/bin/bash
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
echo "============ SMOKE v9 ============"
python3 smoke_v9.py
echo "============ SMOKE v10 ============"
python3 smoke_v10.py
echo "============ SMOKE v11 ============"
python3 smoke_v11.py
echo "============ SMOKE v17 (orchestrator P0) ============"
python3 tools/smoke_v17.py
echo "============ SMOKE v18 (vocal_fx + sidechain + audit) ============"
python3 tools/smoke_v18.py

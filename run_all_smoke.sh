#!/bin/bash
# ZS Music Maker — прогон всех smoke-тестов (AUDIT-FIX: раньше скрипт
# вызывал НЕсуществующие корневые smoke_v9.py / smoke_v10.py / smoke_v11.py,
# которые были удалены/перенесены в tools/. Теперь идём только по
# реально существующим tools/smoke_v*.py.)
set -u
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

cd "$(dirname "$0")"

PASS=0
FAIL=0
for f in tools/smoke_v*.py; do
    echo "============ $f ============"
    if python3 "$f"; then
        PASS=$((PASS+1))
    else
        echo "[FAIL] $f (exit=$?)"
        FAIL=$((FAIL+1))
    fi
done

echo "================================================"
echo "SMOKE SUMMARY: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
    pwd
)"

cd "$ROOT"

echo "============================================================"
echo "RichmackOS Quality Gate"
echo "============================================================"

echo
echo "=== PYTHON SYNTAX ==="

python3 -m py_compile \
    richmack_metrics/*.py \
    scripts/richmack-metrics \
    tests/*.py

echo "PASS"

echo
echo "=== SHELL SYNTAX ==="

bash -n bin/richmack
bash -n scripts/check-quality.sh

echo "PASS"

echo
echo "=== UNIT / REGRESSION TESTS ==="

PYTHONWARNINGS=error::ResourceWarning \
python3 -m unittest \
    discover \
    -s tests \
    -p 'test_*.py' \
    -v

echo
echo "=== METRICS JSON ==="

python3 scripts/richmack-metrics --json \
    | python3 -m json.tool \
    >/dev/null

echo "PASS"

echo
echo "=== ENGINEERING METRICS ==="

python3 scripts/richmack-metrics

echo
echo "============================================================"
echo "QUALITY GATE PASSED"
echo "============================================================"

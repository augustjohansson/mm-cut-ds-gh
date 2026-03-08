#!/usr/bin/env bash
set -uo pipefail

PASS=0
FAIL=0
SKIP=0

section() {
    echo
    echo "════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "════════════════════════════════════════════════════════════"
}

pass() { echo "  ✓ PASS : $1"; PASS=$((PASS + 1)); }
fail() { echo "  ✗ FAIL : $1"; FAIL=$((FAIL + 1)); }
skip() { echo "  – SKIP : $1"; SKIP=$((SKIP + 1)); }

run_check() {
    local label="$1"; shift
    if "$@" ; then
        pass "$label"
    else
        fail "$label"
    fi
}

SRC_DIR="/opt/src"

section "ufl-cut-ds  –  UFL with cut/ds extensions"

run_check "ufl: import + version" \
    python3 -c "import ufl; print('  version:', ufl.__version__)"

UFL_TEST="$SRC_DIR/ufl-cut-ds/test"
if [ -d "$UFL_TEST" ]; then
    run_check "ufl: pytest suite" \
        python3 -m pytest "$UFL_TEST" -v --tb=short
else
    skip "ufl-cut-ds: test directory not found at $UFL_TEST"
fi

echo
echo "════════════════════════════════════════════════════════════"
echo "  RESULTS: ${PASS} passed   ${FAIL} failed   ${SKIP} skipped"
echo "════════════════════════════════════════════════════════════"

if [ "${FAIL}" -gt 0 ]; then
    echo "  OVERALL: FAILED"
    exit 1
else
    echo "  OVERALL: PASSED"
    exit 0
fi

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

section "dijitso  –  JIT compilation utility"

run_check "dijitso: import + version" \
    python3 -c "import dijitso; print('  version:', dijitso.__version__)"

DIJITSO_TEST="$SRC_DIR/dijitso/test"
if [ -d "$DIJITSO_TEST" ]; then
    run_check "dijitso: serial tests" \
        python3 -m pytest "$DIJITSO_TEST/test_serial_dijitso.py" \
                          "$DIJITSO_TEST/test_system_utils.py" \
                          "$DIJITSO_TEST/test_role_assignment.py" \
                          -v --tb=short
else
    skip "dijitso: test directory not found at $DIJITSO_TEST"
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

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

section "fiat  –  FEniCS Implementation of Automatic Tabulation"

run_check "fiat: import" \
    python3 -c "import FIAT; print('  FIAT imported OK')"

FIAT_TEST="$SRC_DIR/fiat/test"
if [ -d "$FIAT_TEST" ]; then
    run_check "fiat: pytest suite" \
        python3 -m pytest "$FIAT_TEST/unit" -v --tb=short
else
    skip "fiat: test directory not found at $FIAT_TEST"
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

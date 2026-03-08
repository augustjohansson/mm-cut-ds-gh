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

section "instant  –  JIT compilation helper"

run_check "instant: import" \
    python3 -c "import instant; print('  instant imported OK')"

INSTANT_TEST="$SRC_DIR/instant/test"
if [ -d "$INSTANT_TEST" ]; then
    run_check "instant: pytest suite" \
        python3 -m pytest "$INSTANT_TEST" -v --tb=short
else
    skip "instant: test directory not found at $INSTANT_TEST (no formal test suite upstream)"
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

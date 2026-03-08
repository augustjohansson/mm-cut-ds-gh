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

section "ffc-cut-ds  –  FFC with cut/ds extensions"

run_check "ffc: import + version" \
    python3 -c "import ffc; print('  version:', ffc.__version__)"

FFC_UNIT_TEST="$SRC_DIR/ffc-cut-ds/test/unit"
if [ -d "$FFC_UNIT_TEST" ]; then
    run_check "ffc: unit pytest suite" \
        python3 -m pytest "$FFC_UNIT_TEST" -v --tb=short
else
    skip "ffc-cut-ds: test/unit directory not found at $FFC_UNIT_TEST"
fi

FFC_REGRESSION_TEST="$SRC_DIR/ffc-cut-ds/test/regression/test.py"
if [ -f "$FFC_REGRESSION_TEST" ]; then
    echo "  Note: ffc regression tests compile C++ code – this may take several minutes."
    _ffc_rc=0
    (cd "$SRC_DIR/ffc-cut-ds/test/regression" && python3 test.py) || _ffc_rc=$?
    if [ "$_ffc_rc" -eq 0 ]; then
        pass "ffc: regression tests"
    else
        fail "ffc: regression tests"
    fi
else
    skip "ffc-cut-ds: test/regression/test.py not found at $FFC_REGRESSION_TEST"
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

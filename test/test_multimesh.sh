#!/usr/bin/env bash
# Run DOLFIN multimesh tests inside the container built by docker/Dockerfile.
# Output is suitable for capture into a log file:
#
#   docker run --rm dolfin-cut bash /opt/src/dolfin/docker/test_multimesh.sh \
#       | tee multimesh_tests.log
#
set -uo pipefail

# ── Ensure all output is unbuffered and printed immediately ──────────────────
if [ -z "${_UNBUF:-}" ]; then
    export _UNBUF=1
    exec stdbuf -oL -eL "$0" "$@"
fi
export PYTHONUNBUFFERED=1

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

run_demo() {
    local label="$1"
    local demo_dir="$2"
    local exe_name="$3"
    local exe="$demo_dir/$exe_name"

    if [ ! -d "$demo_dir" ]; then
        skip "$label: demo build directory not found: $demo_dir"
        return
    fi
    if [ ! -x "$exe" ]; then
        skip "$label: demo binary not found: $exe"
        return
    fi

    local tmpdir
    tmpdir=$(mktemp -d)
    mkdir -p "$tmpdir/output"
    local demo_rc=0
    (cd "$tmpdir" && "$exe") || demo_rc=$?
    rm -rf "$tmpdir"

    if [ "$demo_rc" -eq 0 ]; then
        pass "$label"
    else
        fail "$label"
    fi
}

SRC_DIR="/opt/src"
DOLFIN_BUILD_DIR="/opt/build/dolfin"
DOLFIN_SRC_DIR="$SRC_DIR/dolfin"

section "dolfin C++ unit tests  –  multimesh"

UNITTEST_DIR="$DOLFIN_BUILD_DIR/test/unit/cpp"
UNITTEST_BIN="$UNITTEST_DIR/unittests"

if [ -x "$UNITTEST_BIN" ]; then
    cd "$UNITTEST_DIR" || exit 1

    # ---- MultiMesh (MultiMesh.cpp) ----
    run_check "dolfin C++: MultiMesh tests" \
        "$UNITTEST_BIN" "MultiMesh"

    cd - > /dev/null || exit 1
else
    fail "dolfin C++ unittests binary not found: $UNITTEST_BIN"
fi

section "dolfin Python unit tests  –  multimesh"

DOLFIN_PY_MM_TEST="$DOLFIN_SRC_DIR/python/test/unit/multimesh"
if [ -d "$DOLFIN_PY_MM_TEST" ]; then
    run_check "dolfin Python: multimesh tests" \
        python3 -u -m pytest "$DOLFIN_PY_MM_TEST" -v --tb=short
else
    skip "dolfin Python multimesh tests not found: $DOLFIN_PY_MM_TEST"
fi

section "dolfin C++ demos  –  multimesh + geometry"

DEMO_BASE="$DOLFIN_BUILD_DIR/demo"

echo "  Note: multimesh-poisson runs 100 time steps – this may take a few minutes."
run_demo "demo: multimesh-poisson (C++)" \
    "$DEMO_BASE/undocumented/multimesh-poisson/cpp" \
    "demo_multimesh-poisson"

run_demo "demo: multimesh-stokes (C++)" \
    "$DEMO_BASE/undocumented/multimesh-stokes/cpp" \
    "demo_multimesh-stokes"

if [ -x "$DEMO_BASE/undocumented/multimesh-3d/cpp/demo_multimesh-3d" ]; then
    run_demo "demo: multimesh-3d (C++)" \
        "$DEMO_BASE/undocumented/multimesh-3d/cpp" \
        "demo_multimesh-3d"
else
    fail "demo: multimesh-3d binary not found (expected to be built)"
fi

run_demo "demo: nonmatching-interpolation (C++)" \
    "$DEMO_BASE/documented/nonmatching-interpolation/cpp" \
    "demo_nonmatching-interpolation"

for mv_name in meshview-2D2D meshview-3D1D meshview-3D2D meshview-3D3D; do
    if [ -x "$DEMO_BASE/undocumented/$mv_name/cpp/demo_$mv_name" ]; then
        run_demo "demo: $mv_name (C++)" \
            "$DEMO_BASE/undocumented/$mv_name/cpp" \
            "demo_$mv_name"
    else
        fail "demo: $mv_name binary not found (expected to be built)"
    fi
done

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

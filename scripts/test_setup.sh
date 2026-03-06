#!/usr/bin/env bash
# test_setup.sh
#
# Validates the mm-cut-ds FEniCS environment by running tests and selected demos.
#
# Intended to be run inside the Docker container:
#
#   docker run --rm ghcr.io/augustjohansson/mm-cut-ds-gh:latest bash /work/scripts/test_setup.sh
#
# Or, if the repository is mounted:
#
#   docker run --rm -v $PWD:/work ghcr.io/augustjohansson/mm-cut-ds-gh:latest bash /work/scripts/test_setup.sh
#
# Packages tested:
#   - dijitso   (serial tests + import check)
#   - instant   (import check)
#   - ufl-cut-ds (pytest suite)
#   - fiat      (pytest suite)
#   - ffc-cut-ds (pytest unit tests)
#   - dolfin C++ unit tests: geometry (ConvexTriangulation, IntersectionConstruction)
#                            and mesh/MultiMesh
#   - dolfin C++ demos: multimesh-poisson, multimesh-stokes, nonmatching-interpolation
#                       multimesh-3d (if built), meshview-* (if built)
#   - dolfin Python unit tests: mesh/test_meshview.py

set -uo pipefail

# ── Counters ──────────────────────────────────────────────────────────────────
PASS=0
FAIL=0
SKIP=0

# ── Helpers ───────────────────────────────────────────────────────────────────
section() {
    echo
    echo "════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "════════════════════════════════════════════════════════════"
}

pass() { echo "  ✓ PASS : $1"; PASS=$((PASS + 1)); }
fail() { echo "  ✗ FAIL : $1"; FAIL=$((FAIL + 1)); }
skip() { echo "  – SKIP : $1"; SKIP=$((SKIP + 1)); }

# Run a command, report pass/fail, never abort the overall script.
run_check() {
    local label="$1"; shift
    if "$@" ; then
        pass "$label"
    else
        fail "$label"
    fi
}

# ── Paths ─────────────────────────────────────────────────────────────────────
SRC_DIR="/opt/src"
DOLFIN_BUILD_DIR="/opt/build/dolfin"
DOLFIN_SRC_DIR="$SRC_DIR/dolfin-cut-ds"

# ══════════════════════════════════════════════════════════════════════════════
# 1. dijitso
# ══════════════════════════════════════════════════════════════════════════════
section "1. dijitso  –  JIT compilation utility"

run_check "dijitso: import + version" \
    python3 -c "import dijitso; print('  version:', dijitso.__version__)"

DIJITSO_TEST="$SRC_DIR/dijitso/test"
if [ -d "$DIJITSO_TEST" ]; then
    # Run serial tests only (MPI tests require a working mpirun configuration)
    run_check "dijitso: serial tests" \
        python3 -m pytest "$DIJITSO_TEST/test_serial_dijitso.py" \
                          "$DIJITSO_TEST/test_system_utils.py" \
                          "$DIJITSO_TEST/test_role_assignment.py" \
                          -v --tb=short
else
    skip "dijitso: test directory not found at $DIJITSO_TEST"
fi

# ══════════════════════════════════════════════════════════════════════════════
# 2. instant
# ══════════════════════════════════════════════════════════════════════════════
section "2. instant  –  JIT compilation helper"

run_check "instant: import" \
    python3 -c "import instant; print('  instant imported OK')"

INSTANT_TEST="$SRC_DIR/instant/test"
if [ -d "$INSTANT_TEST" ]; then
    run_check "instant: pytest suite" \
        python3 -m pytest "$INSTANT_TEST" -v --tb=short
else
    skip "instant: test directory not found at $INSTANT_TEST (no formal test suite upstream)"
fi

# ══════════════════════════════════════════════════════════════════════════════
# 3. ufl-cut-ds
# ══════════════════════════════════════════════════════════════════════════════
section "3. ufl-cut-ds  –  UFL with cut/ds extensions"

run_check "ufl: import + version" \
    python3 -c "import ufl; print('  version:', ufl.__version__)"

UFL_TEST="$SRC_DIR/ufl-cut-ds/test"
if [ -d "$UFL_TEST" ]; then
    run_check "ufl: pytest suite" \
        python3 -m pytest "$UFL_TEST" -v --tb=short
else
    skip "ufl-cut-ds: test directory not found at $UFL_TEST"
fi

# ══════════════════════════════════════════════════════════════════════════════
# 4. fiat
# ══════════════════════════════════════════════════════════════════════════════
section "4. fiat  –  FEniCS Implementation of Automatic Tabulation"

run_check "fiat: import" \
    python3 -c "import FIAT; print('  FIAT imported OK')"

FIAT_TEST="$SRC_DIR/fiat/test"
if [ -d "$FIAT_TEST" ]; then
    run_check "fiat: pytest suite" \
        python3 -m pytest "$FIAT_TEST/unit" -v --tb=short
else
    skip "fiat: test directory not found at $FIAT_TEST"
fi

# ══════════════════════════════════════════════════════════════════════════════
# 5. ffc-cut-ds
# ══════════════════════════════════════════════════════════════════════════════
section "5. ffc-cut-ds  –  FFC with cut/ds extensions"

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
    # Regression tests use a custom test runner (not pytest); they compile UFC code
    # and compare C++ output against reference data.  They are long-running (~minutes).
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

# ══════════════════════════════════════════════════════════════════════════════
# 6. dolfin C++ unit tests  –  geometry and multimesh
# ══════════════════════════════════════════════════════════════════════════════
section "6. dolfin C++ unit tests  –  geometry + multimesh"

UNITTEST_DIR="$DOLFIN_BUILD_DIR/test/unit/cpp"
UNITTEST_BIN="$UNITTEST_DIR/unittests"

if [ -x "$UNITTEST_BIN" ]; then
    cd "$UNITTEST_DIR"

    # Geometry: ConvexTriangulation (no [!hide] tag – runs by default)
    run_check "dolfin C++: ConvexTriangulation geometry tests" \
        "$UNITTEST_BIN" "Convex triangulation test"

    # Geometry: IntersectionConstruction (no [!hide] tag – runs by default)
    run_check "dolfin C++: IntersectionConstruction geometry tests" \
        "$UNITTEST_BIN" "Intersection construction test"

    # MultiMesh (tagged [!hide]; explicitly invoked by test-case name)
    # Note: these tests are marked DISABLED/FIXME in source; failures are expected.
    echo "  Note: MultiMesh C++ tests are tagged [!hide] and marked as work-in-progress."
    if "$UNITTEST_BIN" "MultiMesh" 2>&1; then
        pass "dolfin C++: MultiMesh tests"
    else
        echo "  (MultiMesh test failure recorded but not blocking – known WIP)"
        fail "dolfin C++: MultiMesh tests"
    fi

    cd - > /dev/null
else
    fail "dolfin C++ unittests binary not found: $UNITTEST_BIN"
fi

# ══════════════════════════════════════════════════════════════════════════════
# 7. dolfin Python unit tests  –  meshview
# ══════════════════════════════════════════════════════════════════════════════
section "7. dolfin Python unit tests  –  meshview"

DOLFIN_PY_MESH_TEST="$DOLFIN_SRC_DIR/test/unit/python/mesh/test_meshview.py"
if [ -f "$DOLFIN_PY_MESH_TEST" ]; then
    # Make sure the dolfin Python bindings are available
    export PYTHONPATH="$DOLFIN_BUILD_DIR/python:${PYTHONPATH:-}"
    run_check "dolfin Python: test_meshview" \
        python3 -m pytest "$DOLFIN_PY_MESH_TEST" -v --tb=short
else
    skip "dolfin Python meshview test not found: $DOLFIN_PY_MESH_TEST"
fi

# ══════════════════════════════════════════════════════════════════════════════
# 8. dolfin C++ demos  –  multimesh and geometry
# ══════════════════════════════════════════════════════════════════════════════
section "8. dolfin C++ demos  –  multimesh + geometry"

DEMO_BASE="$DOLFIN_BUILD_DIR/demo"

# Helper: run a demo binary from a temporary working directory.
# The demo name, source dir, and binary name are given as arguments.
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

    # Run from a temp dir so relative paths (e.g., "output/") are isolated.
    # Use a subshell only for the cd+exec; capture exit code in the parent.
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

# ── Multimesh demos ────────────────────────────────────────────────────────
# multimesh-poisson: solves Poisson on 3 overlapping meshes, 100 time steps.
# Expect runtime: 1–3 minutes on modern hardware.
echo "  Note: multimesh-poisson runs 100 time steps – this may take a few minutes."
run_demo "demo: multimesh-poisson (C++)" \
    "$DEMO_BASE/undocumented/multimesh-poisson/cpp" \
    "demo_multimesh-poisson"

# multimesh-stokes: MultiMesh Stokes demo.
run_demo "demo: multimesh-stokes (C++)" \
    "$DEMO_BASE/undocumented/multimesh-stokes/cpp" \
    "demo_multimesh-stokes"

# multimesh-3d: 3D multimesh demo (not in the standard CMakeLists; built if present).
if [ -x "$DEMO_BASE/undocumented/multimesh-3d/cpp/demo_multimesh-3d" ]; then
    run_demo "demo: multimesh-3d (C++)" \
        "$DEMO_BASE/undocumented/multimesh-3d/cpp" \
        "demo_multimesh-3d"
else
    skip "demo: multimesh-3d not in standard build (not listed in demo/CMakeLists.txt)"
fi

# ── Geometry / non-matching demos ─────────────────────────────────────────
run_demo "demo: nonmatching-interpolation (C++)" \
    "$DEMO_BASE/documented/nonmatching-interpolation/cpp" \
    "demo_nonmatching-interpolation"

# ── Meshview demos (cut-ds specific; not in standard CMakeLists) ──────────
for mv_name in meshview-2D2D meshview-3D1D meshview-3D2D meshview-3D3D; do
    if [ -x "$DEMO_BASE/undocumented/$mv_name/cpp/demo_$mv_name" ]; then
        run_demo "demo: $mv_name (C++)" \
            "$DEMO_BASE/undocumented/$mv_name/cpp" \
            "demo_$mv_name"
    else
        skip "demo: $mv_name not in standard build (not listed in demo/CMakeLists.txt)"
    fi
done

# ══════════════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════════════
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

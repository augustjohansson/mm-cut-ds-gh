#!/usr/bin/env bash
# Run DOLFIN geometry tests inside the container built by docker/Dockerfile.
# Output is suitable for capture into a log file:
#
#   docker run --rm dolfin-cut bash /opt/src/dolfin/docker/test_geometry.sh \
#       | tee geometry_tests.log
#
# CGAL geometry switch:
#   The DOLFIN build flag -DDOLFIN_USE_CGAL controls which geometry backend
#   is used for all predicates and intersection routines:
#
#     -DDOLFIN_USE_CGAL=OFF  (default)
#         Uses Shewchuk exact predicates (built in, no CGAL dependency).
#         The [cgal] C++ unit tests are compiled but produce zero test
#         cases at run time, so they exit 0 (PASS).
#
#     -DDOLFIN_USE_CGAL=ON
#         Uses CGAL EPICK predicates and CGAL intersection routines.
#         The [cgal] C++ unit tests are compiled and run, verifying that
#         CGAL and Shewchuk give identical results.
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

SRC_DIR="/opt/src"
DOLFIN_BUILD_DIR="/opt/build/dolfin"
DOLFIN_SRC_DIR="$SRC_DIR/dolfin"

section "dolfin C++ unit tests  –  geometry"

UNITTEST_DIR="$DOLFIN_BUILD_DIR/test/unit/cpp"
UNITTEST_BIN="$UNITTEST_DIR/unittests"

if [ -x "$UNITTEST_BIN" ]; then
    cd "$UNITTEST_DIR" || exit 1

    # ---- Convex triangulation (testConvexTriangulation.cpp) ----
    run_check "dolfin C++: ConvexTriangulation geometry tests" \
        "$UNITTEST_BIN" "Convex triangulation test"

    # ---- Intersection construction (testIntersectionConstruction.cpp) ----
    run_check "dolfin C++: IntersectionConstruction geometry tests" \
        "$UNITTEST_BIN" "Intersection construction test"

    # ---- Collision predicates (testCollisionPredicates.cpp) ----
    run_check "dolfin C++: CollisionPredicates tests" \
        "$UNITTEST_BIN" "CollisionPredicates*"

    # ---- Simplex quadrature (testSimplexQuadrature.cpp) ----
    run_check "dolfin C++: SimplexQuadrature tests" \
        "$UNITTEST_BIN" "SimplexQuadrature*"

    # ---- Quadrature compression (testSimplexQuadrature.cpp) ----
    run_check "dolfin C++: Compression tests" \
        "$UNITTEST_BIN" "Compression*"

    # ---- CGAL comparison (testCGALComparison.cpp) ----
    run_check "dolfin C++: CGAL comparison tests (skipped when CGAL is off)" \
        "$UNITTEST_BIN" "[cgal]"

    cd - > /dev/null || exit 1
else
    fail "dolfin C++ unittests binary not found: $UNITTEST_BIN"
fi

section "dolfin Python unit tests  –  meshview"

DOLFIN_PY_MESH_TEST="$DOLFIN_SRC_DIR/test/unit/python/mesh/test_meshview.py"
if [ -f "$DOLFIN_PY_MESH_TEST" ]; then
    export PYTHONPATH="$DOLFIN_BUILD_DIR/python:${PYTHONPATH:-}"
    run_check "dolfin Python: test_meshview" \
        python3 -u -m pytest "$DOLFIN_PY_MESH_TEST" -v --tb=short
else
    skip "dolfin Python meshview test not found: $DOLFIN_PY_MESH_TEST"
fi

section "dolfin Python unit tests  –  geometry"

DOLFIN_PY_GEO_TEST="$DOLFIN_SRC_DIR/python/test/unit/geometry"
if [ -d "$DOLFIN_PY_GEO_TEST" ]; then
    run_check "dolfin Python: geometry tests" \
        python3 -u -m pytest "$DOLFIN_PY_GEO_TEST" -v --tb=short
else
    skip "dolfin Python geometry tests not found: $DOLFIN_PY_GEO_TEST"
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

#!/usr/bin/env bash
set -euo pipefail

repo_url="${DOLFIN_REPO_URL:-https://github.com/augustjohansson/dolfin-cut-ds-no-lfs.git}"
branch="${DOLFIN_BRANCH:-main}"
src_dir="${DOLFIN_SRC_DIR:-/opt/src/dolfin}"
build_dir="${DOLFIN_BUILD_DIR:-/opt/build/dolfin}"
install_prefix="${DOLFIN_INSTALL_PREFIX:-/usr/local}"
build_type="${DOLFIN_BUILD_TYPE:-RelWithDebInfo}"
use_cgal="${DOLFIN_USE_CGAL:-OFF}"
jobs="${DOLFIN_JOBS:-$(nproc)}"

# "Fetching/updating DOLFIN
if [[ -d "${src_dir}/.git" ]]; then
    git -C "${src_dir}" fetch origin
    git -C "${src_dir}" checkout "${branch}"
    git -C "${src_dir}" pull --ff-only origin "${branch}"
else
    rm -rf "${src_dir}"
    git clone --depth 1 --single-branch --branch "${branch}" "${repo_url}" "${src_dir}"
fi

# Configuring DOLFIN
mkdir -p "${build_dir}"
cd "${build_dir}"

if ! cmake -G Ninja "${src_dir}" \
    -DCMAKE_BUILD_TYPE="${build_type}" \
    -DCMAKE_INSTALL_PREFIX="${install_prefix}" \
    -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
    -DDOLFIN_USE_CGAL="${use_cgal}" \
    -DDOLFIN_ENABLE_TESTS=ON \
    -DDOLFIN_ENABLE_DEMO=ON \
    -DDOLFIN_ENABLE_BENCHMARKS=OFF
then
    echo "---- CMakeError.log ----"
    cat CMakeFiles/CMakeError.log || true
    echo "---- CMakeOutput.log ----"
    cat CMakeFiles/CMakeOutput.log || true
    exit 1
fi

# Building DOLFIN
ninja -j"${jobs}"

# Building selected tests and demos
ninja -j"${jobs}" \
    test/unit/cpp/unittests \
    demo/undocumented/multimesh-poisson/cpp/demo_multimesh-poisson \
    demo/undocumented/multimesh-stokes/cpp/demo_multimesh-stokes \
    demo/undocumented/multimesh-3d/cpp/demo_multimesh-3d \
    demo/documented/nonmatching-interpolation/cpp/demo_nonmatching-interpolation

# Installing DOLFIN
ninja install
ldconfig

# Installing DOLFIN Python bindings
cd "${src_dir}/python"
PYBIND11_DIR="$(python3 -c 'import pybind11; print(pybind11.get_cmake_dir(), end="")')" \
python3 -m pip install --no-cache-dir --no-deps --no-build-isolation .

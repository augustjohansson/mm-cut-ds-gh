FROM ubuntu:22.04

SHELL ["/bin/bash", "-lc"]
ENV DEBIAN_FRONTEND=noninteractive

ENV GIT_LFS_SKIP_SMUDGE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git \
    build-essential cmake ninja-build pkg-config ccache \
    swig \
    python3 python3-dev python3-pip python3-setuptools python3-wheel \
    libopenmpi-dev openmpi-bin \
    libpetsc-real-dev \
    libhdf5-openmpi-dev \
    libboost-all-dev \
    libeigen3-dev \
    zlib1g-dev \
    libcgal-dev libgmp-dev libmpfr-dev \
    freecad-python3 \
    python3-gmsh python3-meshio python3-h5py \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/usr/lib/freecad-python3/lib

RUN python3 -m pip install --no-cache-dir -U pip setuptools wheel
RUN python3 -m pip install --no-cache-dir -U "numpy<2" pytest pybind11 mpi4py pkgconfig decorator && \
    python3 -m pip install --no-cache-dir --ignore-installed "sympy==1.10.1"

WORKDIR /opt/src

COPY intersection_dispatch.cpp /tmp/intersection_dispatch.cpp
COPY patch_dolfin_tests.py /tmp/patch_dolfin_tests.py

RUN git clone --depth 1 --single-branch --branch main \
    https://github.com/augustjohansson/dolfin-cut-ds-no-lfs.git dolfin
RUN git clone --depth 1 --single-branch --branch august/mergebb \
    https://github.com/augustjohansson/ffc-cut-ds.git
RUN git clone --depth 1 --single-branch --branch august/merge-legacy \
    https://github.com/augustjohansson/ufl-test.git ufl-cut-ds
RUN git clone --depth 1 --single-branch --branch master \
    https://github.com/augustjohansson/dijitso.git
RUN git clone --depth 1 --single-branch --branch master \
    https://github.com/augustjohansson/instant.git
RUN git clone --depth 1 --single-branch --branch master \
    https://github.com/augustjohansson/fiat.git
RUN git clone --depth 1 --single-branch --branch master \
    https://github.com/augustjohansson/mshr.git

RUN cd /opt/src/dijitso && python3 -m pip install --no-cache-dir --no-deps .
RUN cd /opt/src/instant && python3 -m pip install --no-cache-dir --no-deps .
RUN cd /opt/src/ufl-cut-ds && python3 -m pip install --no-cache-dir --no-deps .
RUN cd /opt/src/fiat && python3 -m pip install --no-cache-dir --no-deps .
RUN cd /opt/src/ffc-cut-ds && python3 -m pip install --no-cache-dir --no-deps .

# Build ffc_factory (C++ extension needed by ffc-cut-ds test_evaluate)
RUN cd /opt/src/ffc-cut-ds/libs/ffc-factory && \
    python3 setup.py build_ext --inplace && \
    cp ffc_factory*.so /usr/local/lib/python3.10/dist-packages/

RUN cd /opt/src/dolfin && git pull && \
    cat /tmp/intersection_dispatch.cpp >> dolfin/geometry/IntersectionConstruction.cpp && \
    python3 /tmp/patch_dolfin_tests.py && \
    mkdir -p /opt/build/dolfin && cd /opt/build/dolfin && \
    cmake -G Ninja /opt/src/dolfin \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
    -DDOLFIN_USE_CGAL=OFF \
    -DDOLFIN_ENABLE_TESTS=ON \
    -DDOLFIN_ENABLE_DEMO=ON \
    -DDOLFIN_ENABLE_BENCHMARKS=OFF \
    || (echo "---- CMakeError.log ----" && cat CMakeFiles/CMakeError.log || true; \
    echo "---- CMakeOutput.log ----" && cat CMakeFiles/CMakeOutput.log || true; \
    exit 1) && \
    ninja -j"$(nproc)" && \
    ninja -j"$(nproc)" \
        test/unit/cpp/unittests \
        demo/undocumented/multimesh-poisson/cpp/demo_multimesh-poisson \
        demo/undocumented/multimesh-stokes/cpp/demo_multimesh-stokes \
        demo/documented/nonmatching-interpolation/cpp/demo_nonmatching-interpolation && \
    ninja install && \
    ldconfig

# Build/install dolfin Python bindings
RUN cd /opt/src/dolfin/python && \
    PYBIND11_DIR=$(python3 -c "import pybind11; print(pybind11.get_cmake_dir(), end='')") \
    python3 -m pip install --no-cache-dir --no-deps --no-build-isolation .

# # ----- Build/install mshr -----
# RUN mkdir -p /opt/build/mshr && cd /opt/build/mshr && \
#     cmake -G Ninja /opt/src/mshr \
#       -DCMAKE_BUILD_TYPE=RelWithDebInfo \
#       -DCMAKE_INSTALL_PREFIX=/usr/local \
#       -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
#     || (echo "---- CMakeError.log ----" && cat CMakeFiles/CMakeError.log || true; \
#	echo "---- CMakeOutput.log ----" && cat CMakeFiles/CMakeOutput.log || true; \
#	exit 1) && \
#     ninja -j"$(nproc)" && \
#     ninja install && \
#     ldconfig

WORKDIR /work
CMD ["bash"]

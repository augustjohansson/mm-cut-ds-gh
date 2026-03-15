# syntax=docker/dockerfile:1
FROM ubuntu:22.04

SHELL ["/bin/bash", "-lc"]
ENV DEBIAN_FRONTEND=noninteractive
ENV GIT_LFS_SKIP_SMUDGE=1
ENV PYTHONPATH=/usr/lib/freecad-python3/lib
ENV CCACHE_DIR=/root/.cache/ccache
ENV CCACHE_MAXSIZE=10G

WORKDIR /opt/src

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
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

RUN --mount=type=cache,target=/root/.cache/pip \
    python3 -m pip install -U pip setuptools wheel && \
    python3 -m pip install -U "numpy<2" pytest pybind11 mpi4py pkgconfig decorator && \
    python3 -m pip install --ignore-installed "sympy==1.10.1"

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
# RUN git clone --depth 1 --single-branch --branch master \
#     https://github.com/augustjohansson/mshr.git

RUN --mount=type=cache,target=/root/.cache/pip \
    cd /opt/src/dijitso && python3 -m pip install --no-deps .
RUN --mount=type=cache,target=/root/.cache/pip \
    cd /opt/src/instant && python3 -m pip install --no-deps .
RUN --mount=type=cache,target=/root/.cache/pip \
    cd /opt/src/ufl-cut-ds && python3 -m pip install --no-deps .
RUN --mount=type=cache,target=/root/.cache/pip \
    cd /opt/src/fiat && python3 -m pip install --no-deps .
RUN --mount=type=cache,target=/root/.cache/pip \
    cd /opt/src/ffc-cut-ds && python3 -m pip install --no-deps .

RUN cd /opt/src/ffc-cut-ds/libs/ffc-factory && \
    python3 setup.py build_ext --inplace && \
    cp ffc_factory*.so /usr/local/lib/python3.10/dist-packages/

COPY docker/fetch-build-dolfin.sh /usr/local/bin/fetch-build-dolfin
RUN chmod +x /usr/local/bin/fetch-build-dolfin

ARG DOLFIN_USE_CGAL=ON
ARG DOLFIN_CACHE_BUST=0
RUN --mount=type=cache,target=/root/.cache/ccache \
    --mount=type=cache,target=/root/.cache/pip \
    echo "${DOLFIN_CACHE_BUST}" >/dev/null && fetch-build-dolfin

WORKDIR /work
CMD ["bash"]

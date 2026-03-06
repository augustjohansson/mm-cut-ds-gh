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
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir -U pip setuptools wheel
RUN python3 -m pip install --no-cache-dir -U "numpy<2" "sympy==1.10.1"

WORKDIR /opt/src

RUN git clone --depth 1 --single-branch --branch august/mergebb \
    https://github.com/augustjohansson/dolfin-cut-ds.git
RUN git clone --depth 1 --single-branch --branch august/mergebb \
    https://github.com/augustjohansson/ffc-cut-ds.git
RUN git clone --depth 1 --single-branch --branch august/merge-legacy \
    https://github.com/augustjohansson/ufl-test.git
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

RUN cd /opt/src/dolfin-cut-ds && git pull && \
    mkdir -p /opt/build/dolfin && cd /opt/build/dolfin && \
    cmake -G Ninja /opt/src/dolfin-cut-ds \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_INSTALL_PREFIX=/usr/local \
      -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
      -DDOLFIN_ENABLE_TESTS=ON \
      -DDOLFIN_ENABLE_DEMO=ON \
      -DDOLFIN_ENABLE_BENCHMARKS=OFF \
    || (echo "---- CMakeError.log ----" && cat CMakeFiles/CMakeError.log || true; \
	echo "---- CMakeOutput.log ----" && cat CMakeFiles/CMakeOutput.log || true; \
	exit 1) && \
    ninja -j"$(nproc)" && \
    ninja install && \
    ldconfig

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

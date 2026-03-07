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
RUN python3 -m pip install --no-cache-dir -U "numpy<2" "sympy==1.10.1" pytest pybind11

WORKDIR /opt/src

RUN git clone --depth 1 --single-branch --branch august/mergebb \
    https://github.com/augustjohansson/dolfin-cut-ds.git
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

# ── Patch instant: replace "six" dependency with Python 3 builtins ────────────
RUN cd /opt/src/instant && \
    sed -i 's/^from six import string_types$/string_types = str/' \
	instant/output.py instant/paths.py instant/config.py instant/signatures.py && \
    sed -i 's/^import six$//' instant/build.py && \
    sed -i 's/^from six import string_types$/string_types = str/' instant/build.py

# # ── Patch fiat: fix pytest compatibility for newer pytest versions ────────────
# # 1) test_quadrature.py: replace direct fixture calls with plain constructors
# RUN cd /opt/src/fiat && \
#     sed -i \
#       's/^@pytest.mark.parametrize("cell", \[interval(),/@pytest.mark.parametrize("cell", [UFCInterval(),/' \
#       test/unit/test_quadrature.py && \
#     sed -i \
#       's/^                                  triangle(),$/                                  UFCTriangle(),/' \
#       test/unit/test_quadrature.py && \
#     sed -i \
#       's/^                                  tetrahedron(),$/                                  UFCTetrahedron(),/' \
#       test/unit/test_quadrature.py && \
#     sed -i \
#       's/^                                  quadrilateral()\])$/                                  UFCQuadrilateral()])/' \
#       test/unit/test_quadrature.py && \
#     sed -i \
#       's/^@pytest.mark.parametrize("cell", \[extr_interval(),/@pytest.mark.parametrize("cell", [TensorProductCell(UFCInterval(), UFCInterval()),/' \
#       test/unit/test_quadrature.py && \
#     sed -i \
#       's/^                                  extr_triangle(),$/                                  TensorProductCell(UFCTriangle(), UFCInterval()),/' \
#       test/unit/test_quadrature.py && \
#     sed -i \
#       's/^                                  extr_quadrilateral()\])$/                                  TensorProductCell(UFCQuadrilateral(), UFCInterval())])/' \
#       test/unit/test_quadrature.py

# # 2) test_reference_element.py: replace old-style pytest.mark.xfail() with pytest.param()
# RUN cd /opt/src/fiat/test/unit && python3 -c "\
# import re, pathlib; \
# p = pathlib.Path('test_reference_element.py'); \
# txt = p.read_text(); \
# txt = re.sub(r'pytest\.mark\.xfail\(\(([^)]*)\)\)', r'pytest.param(\1, marks=pytest.mark.xfail)', txt); \
# txt = re.sub(r'pytest\.mark\.xfail\(([A-Za-z_][A-Za-z0-9_]*)\)', r'pytest.param(\1, marks=pytest.mark.xfail)', txt); \
# p.write_text(txt)"

# # 3) test_fiat.py: replace xfail_impl("string") with pytest.param("string", marks=xfail_impl)
# COPY docker/patches/fix_fiat_xfail.py /tmp/fix_fiat_xfail.py
# RUN python3 /tmp/fix_fiat_xfail.py /opt/src/fiat/test/unit/test_fiat.py && rm /tmp/fix_fiat_xfail.py

# # 4) test_discontinuous_taylor.py and test_discontinuous_pc.py: replace np.float() with float()
# RUN cd /opt/src/fiat/test/unit && \
#     sed -i 's/np\.float(/float(/g' test_discontinuous_taylor.py test_discontinuous_pc.py

# ── Install Python packages ──────────────────────────────────────────────────
RUN cd /opt/src/dijitso && python3 -m pip install --no-cache-dir --no-deps .
RUN cd /opt/src/instant && python3 -m pip install --no-cache-dir --no-deps .
RUN cd /opt/src/ufl-cut-ds && python3 -m pip install --no-cache-dir --no-deps .
RUN cd /opt/src/fiat && python3 -m pip install --no-cache-dir --no-deps .
RUN cd /opt/src/ffc-cut-ds && python3 -m pip install --no-cache-dir --no-deps .

# ── Build ffc_factory (C++ extension needed by ffc-cut-ds test_evaluate) ──────
RUN cd /opt/src/ffc-cut-ds/libs/ffc-factory && \
    python3 setup.py build_ext --inplace && \
    cp ffc_factory*.so /usr/local/lib/python3.10/dist-packages/

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

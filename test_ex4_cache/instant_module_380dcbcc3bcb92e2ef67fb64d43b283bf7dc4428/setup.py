
import os
from distutils.core import setup, Extension
name = 'instant_module_380dcbcc3bcb92e2ef67fb64d43b283bf7dc4428'
swig_cmd =r'swig -python -py3 -I/usr/local/lib/python3.10/dist-packages/instant/swig -c++ -fcompact -O -I. -small -py3 instant_module_380dcbcc3bcb92e2ef67fb64d43b283bf7dc4428.i'
os.system(swig_cmd)
sources = ['instant_module_380dcbcc3bcb92e2ef67fb64d43b283bf7dc4428_wrap.cxx']
setup(name = 'instant_module_380dcbcc3bcb92e2ef67fb64d43b283bf7dc4428',
      ext_modules = [Extension('_' + 'instant_module_380dcbcc3bcb92e2ef67fb64d43b283bf7dc4428',
                     sources,
                     include_dirs=['/usr/local/lib/python3.10/dist-packages/numpy/core/include'],
                     library_dirs=[],
                     libraries=[] , extra_compile_args=['-O2'] )])

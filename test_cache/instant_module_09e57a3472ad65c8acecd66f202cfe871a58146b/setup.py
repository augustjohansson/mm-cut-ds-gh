
import os
from distutils.core import setup, Extension
name = 'instant_module_09e57a3472ad65c8acecd66f202cfe871a58146b'
swig_cmd =r'swig -python -py3 -I/usr/local/lib/python3.10/dist-packages/instant/swig -c++ -fcompact -O -I. -small -py3 instant_module_09e57a3472ad65c8acecd66f202cfe871a58146b.i'
os.system(swig_cmd)
sources = ['instant_module_09e57a3472ad65c8acecd66f202cfe871a58146b_wrap.cxx']
setup(name = 'instant_module_09e57a3472ad65c8acecd66f202cfe871a58146b',
      ext_modules = [Extension('_' + 'instant_module_09e57a3472ad65c8acecd66f202cfe871a58146b',
                     sources,
                     include_dirs=['/usr/local/lib/python3.10/dist-packages/numpy/core/include'],
                     library_dirs=[],
                     libraries=[] , extra_compile_args=['-g'] )])

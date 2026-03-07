
import os
from distutils.core import setup, Extension
name = 'instant_module_13e1c5a7533e08f1b8225a1bce5cc844ec4cc4ec'
swig_cmd =r'swig -python -py3 -I/usr/local/lib/python3.10/dist-packages/instant/swig -c++ -fcompact -O -I. -small -py3 instant_module_13e1c5a7533e08f1b8225a1bce5cc844ec4cc4ec.i'
os.system(swig_cmd)
sources = ['instant_module_13e1c5a7533e08f1b8225a1bce5cc844ec4cc4ec_wrap.cxx']
setup(name = 'instant_module_13e1c5a7533e08f1b8225a1bce5cc844ec4cc4ec',
      ext_modules = [Extension('_' + 'instant_module_13e1c5a7533e08f1b8225a1bce5cc844ec4cc4ec',
                     sources,
                     include_dirs=['/usr/local/lib/python3.10/dist-packages/numpy/core/include'],
                     library_dirs=[],
                     libraries=[] , extra_compile_args=['-O2'] )])

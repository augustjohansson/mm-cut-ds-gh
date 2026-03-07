
import os
from distutils.core import setup, Extension
name = 'instant_module_410854e79e0f3f05f9f443009565b50785e4e26a'
swig_cmd =r'swig -python -py3 -I/usr/local/lib/python3.10/dist-packages/instant/swig -c++ -fcompact -O -I. -small -py3 instant_module_410854e79e0f3f05f9f443009565b50785e4e26a.i'
os.system(swig_cmd)
sources = ['instant_module_410854e79e0f3f05f9f443009565b50785e4e26a_wrap.cxx']
setup(name = 'instant_module_410854e79e0f3f05f9f443009565b50785e4e26a',
      ext_modules = [Extension('_' + 'instant_module_410854e79e0f3f05f9f443009565b50785e4e26a',
                     sources,
                     include_dirs=['/usr/local/lib/python3.10/dist-packages/numpy/core/include'],
                     library_dirs=[],
                     libraries=[] , extra_compile_args=['-O2'] )])

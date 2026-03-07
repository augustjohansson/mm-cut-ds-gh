
import os
from distutils.core import setup, Extension
name = 'instant_module_980c475d95605c52850dc22efa6e2eb0b123f0e4'
swig_cmd =r'swig -python -py3 -I/usr/local/lib/python3.10/dist-packages/instant/swig -c++ -fcompact -O -I. -small -py3 instant_module_980c475d95605c52850dc22efa6e2eb0b123f0e4.i'
os.system(swig_cmd)
sources = ['instant_module_980c475d95605c52850dc22efa6e2eb0b123f0e4_wrap.cxx']
setup(name = 'instant_module_980c475d95605c52850dc22efa6e2eb0b123f0e4',
      ext_modules = [Extension('_' + 'instant_module_980c475d95605c52850dc22efa6e2eb0b123f0e4',
                     sources,
                     include_dirs=['.'],
                     library_dirs=[],
                     libraries=[] , extra_compile_args=['-O2'] )])

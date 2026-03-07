
import os
from distutils.core import setup, Extension
name = 'instant_module_d329d37b7a34f155ec36923f529a4aea9613c42d'
swig_cmd =r'swig -python -py3 -I/usr/local/lib/python3.10/dist-packages/instant/swig -c++ -fcompact -O -I. -small -py3 instant_module_d329d37b7a34f155ec36923f529a4aea9613c42d.i'
os.system(swig_cmd)
sources = ['instant_module_d329d37b7a34f155ec36923f529a4aea9613c42d_wrap.cxx']
setup(name = 'instant_module_d329d37b7a34f155ec36923f529a4aea9613c42d',
      ext_modules = [Extension('_' + 'instant_module_d329d37b7a34f155ec36923f529a4aea9613c42d',
                     sources,
                     include_dirs=['.'],
                     library_dirs=[],
                     libraries=[] , extra_compile_args=['-O2'] )])

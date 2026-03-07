
import os
from distutils.core import setup, Extension
name = 'test19_ext'
swig_cmd =r'swig -python -py3 -I/usr/local/lib/python3.10/dist-packages/instant/swig -c++ -fcompact -O -I. -small -py3 test19_ext.i'
os.system(swig_cmd)
sources = ['test19_ext_wrap.cxx']
setup(name = 'test19_ext',
      ext_modules = [Extension('_' + 'test19_ext',
                     sources,
                     include_dirs=['.'],
                     library_dirs=[],
                     libraries=[] , extra_compile_args=['-O2'] )])

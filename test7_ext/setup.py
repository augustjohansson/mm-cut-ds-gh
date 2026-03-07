
import os
from distutils.core import setup, Extension
name = 'test7_ext'
swig_cmd =r'swig -python -py3 -I/usr/local/lib/python3.10/dist-packages/instant/swig -c++ -fcompact -O -I. -small -py3 test7_ext.i'
os.system(swig_cmd)
sources = ['test7_ext_wrap.cxx']
setup(name = 'test7_ext',
      ext_modules = [Extension('_' + 'test7_ext',
                     sources,
                     include_dirs=['/usr/local/lib/python3.10/dist-packages/numpy/core/include'],
                     library_dirs=[],
                     libraries=[] , extra_compile_args=['-g'] )])

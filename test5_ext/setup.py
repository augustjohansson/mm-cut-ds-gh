
import os
from distutils.core import setup, Extension
name = 'test5_ext'
swig_cmd =r'swig -python -py3 -I/usr/local/lib/python3.10/dist-packages/instant/swig -c++ -fcompact -O -I. -small -py3 test5_ext.i'
os.system(swig_cmd)
sources = ['test5_ext_wrap.cxx']
setup(name = 'test5_ext',
      ext_modules = [Extension('_' + 'test5_ext',
                     sources,
                     include_dirs=['/usr/local/lib/python3.10/dist-packages/numpy/core/include'],
                     library_dirs=[],
                     libraries=[] , extra_compile_args=['-pg'] , extra_link_args=['-pg'])])

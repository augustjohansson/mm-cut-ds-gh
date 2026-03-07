
import os
from distutils.core import setup, Extension
name = 'test3_ext'
swig_cmd =r'swig -python -py3 -I/usr/local/lib/python3.10/dist-packages/instant/swig -c++ -fcompact -O -I. -small -py3 test3_ext.i'
os.system(swig_cmd)
sources = ['test3_ext_wrap.cxx']
setup(name = 'test3_ext',
      ext_modules = [Extension('_' + 'test3_ext',
                     sources,
                     include_dirs=['.'],
                     library_dirs=[],
                     libraries=[] , extra_compile_args=['-pg', '-O3', '-g'] , extra_link_args=['-pg'])])

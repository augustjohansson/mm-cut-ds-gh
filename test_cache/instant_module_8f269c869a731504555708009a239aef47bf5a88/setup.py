
import os
from distutils.core import setup, Extension
name = 'instant_module_8f269c869a731504555708009a239aef47bf5a88'
swig_cmd =r'swig -python -py3 -I/usr/local/lib/python3.10/dist-packages/instant/swig -c++ -fcompact -O -I. -small -py3 instant_module_8f269c869a731504555708009a239aef47bf5a88.i'
os.system(swig_cmd)
sources = ['instant_module_8f269c869a731504555708009a239aef47bf5a88_wrap.cxx']
setup(name = 'instant_module_8f269c869a731504555708009a239aef47bf5a88',
      ext_modules = [Extension('_' + 'instant_module_8f269c869a731504555708009a239aef47bf5a88',
                     sources,
                     include_dirs=['.'],
                     library_dirs=[],
                     libraries=[] , extra_compile_args=['-O2'] )])

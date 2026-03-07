
import os
from distutils.core import setup, Extension
name = 'instant_module_aa70726a5583758eec36c1904e478800ac5f4597'
swig_cmd =r'swig -python -py3 -I/usr/local/lib/python3.10/dist-packages/instant/swig -c++ -fcompact -O -I. -small -py3 instant_module_aa70726a5583758eec36c1904e478800ac5f4597.i'
os.system(swig_cmd)
sources = ['instant_module_aa70726a5583758eec36c1904e478800ac5f4597_wrap.cxx']
setup(name = 'instant_module_aa70726a5583758eec36c1904e478800ac5f4597',
      ext_modules = [Extension('_' + 'instant_module_aa70726a5583758eec36c1904e478800ac5f4597',
                     sources,
                     include_dirs=['.'],
                     library_dirs=[],
                     libraries=[] , extra_compile_args=['-O2'] )])

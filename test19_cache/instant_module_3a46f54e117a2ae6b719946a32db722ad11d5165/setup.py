
import os
from distutils.core import setup, Extension
name = 'instant_module_3a46f54e117a2ae6b719946a32db722ad11d5165'
swig_cmd =r'swig -python -py3 -I/usr/local/lib/python3.10/dist-packages/instant/swig -c++ -fcompact -O -I. -small -py3 instant_module_3a46f54e117a2ae6b719946a32db722ad11d5165.i'
os.system(swig_cmd)
sources = ['instant_module_3a46f54e117a2ae6b719946a32db722ad11d5165_wrap.cxx']
setup(name = 'instant_module_3a46f54e117a2ae6b719946a32db722ad11d5165',
      ext_modules = [Extension('_' + 'instant_module_3a46f54e117a2ae6b719946a32db722ad11d5165',
                     sources,
                     include_dirs=['.'],
                     library_dirs=[],
                     libraries=[] , extra_compile_args=['-O2'] )])

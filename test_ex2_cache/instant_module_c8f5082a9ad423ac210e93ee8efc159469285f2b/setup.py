
import os
from distutils.core import setup, Extension
name = 'instant_module_c8f5082a9ad423ac210e93ee8efc159469285f2b'
swig_cmd =r'swig -python -py3 -I/usr/local/lib/python3.10/dist-packages/instant/swig -c++ -fcompact -O -I. -small -py3 instant_module_c8f5082a9ad423ac210e93ee8efc159469285f2b.i'
os.system(swig_cmd)
sources = ['instant_module_c8f5082a9ad423ac210e93ee8efc159469285f2b_wrap.cxx']
setup(name = 'instant_module_c8f5082a9ad423ac210e93ee8efc159469285f2b',
      ext_modules = [Extension('_' + 'instant_module_c8f5082a9ad423ac210e93ee8efc159469285f2b',
                     sources,
                     include_dirs=['/usr/local/lib/python3.10/dist-packages/numpy/core/include'],
                     library_dirs=[],
                     libraries=[] , extra_compile_args=['-O2'] )])

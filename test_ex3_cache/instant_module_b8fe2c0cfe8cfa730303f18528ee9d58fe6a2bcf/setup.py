
import os
from distutils.core import setup, Extension
name = 'instant_module_b8fe2c0cfe8cfa730303f18528ee9d58fe6a2bcf'
swig_cmd =r'swig -python -py3 -I/usr/local/lib/python3.10/dist-packages/instant/swig -c++ -fcompact -O -I. -small -py3 instant_module_b8fe2c0cfe8cfa730303f18528ee9d58fe6a2bcf.i'
os.system(swig_cmd)
sources = ['instant_module_b8fe2c0cfe8cfa730303f18528ee9d58fe6a2bcf_wrap.cxx']
setup(name = 'instant_module_b8fe2c0cfe8cfa730303f18528ee9d58fe6a2bcf',
      ext_modules = [Extension('_' + 'instant_module_b8fe2c0cfe8cfa730303f18528ee9d58fe6a2bcf',
                     sources,
                     include_dirs=['/usr/local/lib/python3.10/dist-packages/numpy/core/include'],
                     library_dirs=[],
                     libraries=[] , extra_compile_args=['-O2'] )])

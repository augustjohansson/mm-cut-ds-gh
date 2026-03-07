
import os
from distutils.core import setup, Extension
name = 'instant_module_3059be7129b6e327fcf9090822839500b5a9dcdc'
swig_cmd =r'swig -python -py3 -I/usr/local/lib/python3.10/dist-packages/instant/swig -c++ -fcompact -O -I. -small -py3 instant_module_3059be7129b6e327fcf9090822839500b5a9dcdc.i'
os.system(swig_cmd)
sources = ['instant_module_3059be7129b6e327fcf9090822839500b5a9dcdc_wrap.cxx']
setup(name = 'instant_module_3059be7129b6e327fcf9090822839500b5a9dcdc',
      ext_modules = [Extension('_' + 'instant_module_3059be7129b6e327fcf9090822839500b5a9dcdc',
                     sources,
                     include_dirs=['.'],
                     library_dirs=[],
                     libraries=[] , extra_compile_args=['-O2'] )])

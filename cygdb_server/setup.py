from Cython.Build import cythonize
from setuptools import setup, Extension
import numpy

extensions = Extension('demo', sources=['demo.pyx'],
                       include_dirs=[numpy.get_include()])

setup(
    name='demo',
    url='https://github.com/dfroger/cygdb-demo',
    description='Example of debugging Cython project',
    ext_modules=cythonize(
        extensions,
        gdb_debug=True,
    ),
)

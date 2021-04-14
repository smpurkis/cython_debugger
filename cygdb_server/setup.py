from Cython.Build import cythonize
from setuptools import setup, Extension

extensions = Extension('demo', sources=['demo.pyx'])

setup(
    name='demo',
    url='https://github.com/dfroger/cygdb-demo',
    description='Example of debugging Cython project',
    ext_modules=cythonize(
        extensions,
        gdb_debug=True,
    ),
)

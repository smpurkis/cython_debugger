from Cython.Build import cythonize
from setuptools import setup, Extension
import numpy

extensions = Extension('monte_carlo_simulation', sources=['monte_carlo_simulation.pyx'],
                       include_dirs=[numpy.get_include()])

setup(
    ext_modules=cythonize(
        extensions,
        gdb_debug=True,
    ),
)

# cython: infer_types=True
# distutils: extra_compile_args = -fopenmp -Ofast -ffast-math
# distutils: extra_link_args = -fopenmp -Ofast -ffast-math
cimport cython
from cython import nogil
from cython.parallel import prange
import numpy as np
cimport numpy as np

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.overflowcheck(False)
cpdef estimate_pi_cy(long nMC):
    cdef:
        double radius
        double diameter
        long n_circle
        double x
        double y
        double r
        long i
        double result
        np.ndarray rand_arr_y
        double [:] rand_arr_y_memview
        np.ndarray rand_arr_x
        double [:] rand_arr_x_memview

    rand_arr_y = np.random.rand(nMC) - 0.5
    rand_arr_y_memview = rand_arr_y
    rand_arr_x = np.random.rand(nMC) - 0.5
    rand_arr_x_memview = rand_arr_x

    radius = 1.
    diameter = 2. * radius
    n_circle = 0
    for i in range(nMC):
        x = (rand_arr_x_memview[i]) * diameter
        y = (rand_arr_y_memview[i]) * diameter
        r = (x * x + y * y) ** 0.5
        if r <= radius:
            n_circle += 1
    return 4. * n_circle / nMC
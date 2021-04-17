import numpy as np
cimport numpy as np

cpdef double foo(double x):
    o = 0
    cdef double zxc = 3.0
    zxc = zxc + 2.0
    print()  # empty print to prevent Cython optimizing out this line
    return zxc

cpdef bar(double x):
    print(4*x)
    return 2*x

cpdef double baz(double x, np.ndarray arr, u, li):
    cdef list j = ["hello", "today"]
    cdef dict d = {"name": "hello"}
    cdef int i = 1
    cdef double l = 0.5
    cdef double t
    j.append(5)
    li.append(9)
    t = 0.5
    print(t)
    t = foo(t)
    print(t)
    i = i + 1
    print(i)
    print(x)
    x = x + 1.5
    print(x)
    print(l)
    return 2*x

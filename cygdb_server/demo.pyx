import numpy as np
cimport numpy as np

cdef double foo(double x):
    return 2*x

def bar(double x):
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
    i = i + 1
    print(i)
    print(x)
    x = x + 1.5
    print(x)
    print(l)
    return 2*x

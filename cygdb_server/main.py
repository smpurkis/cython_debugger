import numpy as np

import demo


def test(x):
    x = 1
    x = x + 1
    return x


x2 = 3.
l = [6, 4, 6, 34, 5, 345]
# breakpoint()
test(x2)
y = demo.baz(x2, np.zeros((10, 10)), 8, l)
print(demo.bar(x2))
breakpoint()
print(x2, y)

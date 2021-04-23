
from monte_carlo_simulation import estimate_pi_cy
from time import time

def run():
    print("running run file")

    names = ["sam", "emma", "jeff", "dave"]
    for name in names:
        if name in ["sam", "emma"]:
            print(f"{name} is awesome!")

    n = 10_000_000

    start = time()
    pi = estimate_pi_cy(n)
    print(time() - start)
    print(f"estimate of pi is {pi}")

run()
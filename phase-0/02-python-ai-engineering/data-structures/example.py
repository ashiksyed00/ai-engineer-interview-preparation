"""Runnable examples for core data structures.

Run:  python examples.py
"""

from __future__ import annotations

import copy
import time
from collections import deque
from collections.abc import Iterator
from itertools import islice
from typing import NamedTuple


# --------------------------------------------------------------------- lists
def lists_demo() -> None:
    nums = [5, 2, 9, 1]
    nums.append(7)                      # O(1)
    nums.sort()                         # in place, returns None
    print(nums, sorted(nums, reverse=True))   # sorted() returns a new list
    print(nums[1:3], nums[::-1], nums[-1])    # slicing

    # Gotcha 1: aliasing vs copying
    a = [1, 2, 3]
    b = a                               # same object!
    c = a.copy()                        # new list
    b.append(4)
    print("alias:", a, "copy:", c)

    # Gotcha 2: shallow copy shares nested objects
    grid = [[0, 0], [0, 0]]
    shallow = grid.copy()
    deep = copy.deepcopy(grid)
    grid[0][0] = 99
    print("shallow:", shallow, "deep:", deep)

    # Gotcha 3: [[0]*2]*2 repeats the SAME inner list
    bad = [[0] * 2] * 2
    bad[0][0] = 1
    good = [[0] * 2 for _ in range(2)]
    print("bad:", bad, "good:", good)


# -------------------------------------------------------------------- tuples
class Point(NamedTuple):
    x: float
    y: float


def tuples_demo() -> None:
    p = Point(1.0, 2.0)
    x, y = p                            # unpacking
    print(p, p.x, x + y)
    lookup = {(0, 0): "origin", (1, 2): "A"}   # tuples are hashable -> valid keys
    print(lookup[(1, 2)])


# ---------------------------------------------------------------------- sets
def sets_demo() -> None:
    a, b = {1, 2, 3, 4}, {3, 4, 5}
    print(a | b, a & b, a - b, a ^ b)   # union, intersection, difference, symmetric diff
    print(list(dict.fromkeys([3, 1, 3, 2, 1])))   # dedupe, keep order (sets don't)

    # membership speed: list O(n) vs set O(1)
    big_list = list(range(100_000))
    big_set = set(big_list)
    t0 = time.perf_counter()
    for _ in range(200):
        99_999 in big_list
    t1 = time.perf_counter()
    for _ in range(200):
        99_999 in big_set
    t2 = time.perf_counter()
    print(f"list: {t1 - t0:.4f}s  set: {t2 - t1:.6f}s")


# --------------------------------------------------------------------- dicts
def dicts_demo() -> None:
    user = {"name": "Ada", "age": 36}
    print(user.get("email", "n/a"))                 # no KeyError
    user.setdefault("tags", []).append("ml")        # create-if-missing
    merged = user | {"age": 37}                     # merge (3.9+), right wins
    print(merged)

    for key, value in user.items():                 # iterate pairs
        pass

    inverted = {v: k for k, v in {"a": 1, "b": 2}.items()}
    print(inverted)


# -------------------------------------------------------- iterators/generators
class Countdown:
    """Iterator protocol: __iter__ returns self, __next__ yields or stops."""

    def __init__(self, start: int) -> None:
        self.current = start

    def __iter__(self) -> Iterator[int]:
        return self

    def __next__(self) -> int:
        if self.current <= 0:
            raise StopIteration
        self.current -= 1
        return self.current + 1


def countdown_gen(start: int) -> Iterator[int]:
    """Same thing as a generator: far shorter."""
    while start > 0:
        yield start
        start -= 1


def fib() -> Iterator[int]:
    """Infinite generator: safe because it's lazy."""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


def iter_demo() -> None:
    print(list(Countdown(3)), list(countdown_gen(3)))
    print(list(islice(fib(), 10)))

    gen = (x * x for x in range(3))
    print(list(gen), list(gen))         # generators are single-use: 2nd is empty!


# --------------------------------------------------------------------- deque
def deque_demo() -> None:
    q: deque[int] = deque(maxlen=3)     # fixed-size sliding window
    for i in range(5):
        q.append(i)
    print(q)                            # deque([2, 3, 4], maxlen=3)
    q.appendleft(99)                    # O(1) at both ends (list.insert(0) is O(n))
    print(q.popleft(), q)


if __name__ == "__main__":
    for demo in (lists_demo, tuples_demo, sets_demo, dicts_demo, iter_demo, deque_demo):
        print(f"\n--- {demo.__name__} ---")
        demo()
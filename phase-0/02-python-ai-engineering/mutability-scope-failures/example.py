"""Runnable examples: mutability, scope, exceptions, context managers, failure modes.

Run:  python examples.py
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress

logger = logging.getLogger(__name__)


# ------------------------------------------------- 1. references & mutability
def references_demo() -> None:
    a = [1, 2, 3]
    b = a                        # b is another NAME for the same object
    b.append(4)
    print("a:", a, "| same object:", a is b)

    s = "hi"
    t = s
    t += "!"                     # strings are immutable: creates a NEW string
    print("s:", s, "| t:", t)

    def add_item(items: list[int]) -> None:
        items.append(99)         # mutates the caller's list

    def rebind(items: list[int]) -> None:
        items = [0]              # rebinds the local name only; caller unaffected
        _ = items

    nums = [1]
    add_item(nums)
    rebind(nums)
    print("after calls:", nums)


# ------------------------------------------------------------ 2. scope (LEGB)
counter = 0                      # global


def broken_increment() -> int:
    try:
        counter += 1             # type: ignore[unbound-local]  # assignment makes it local
    except UnboundLocalError as exc:
        return -1 if exc else 0
    return counter


def make_counter() -> Callable[[], int]:
    count = 0

    def inc() -> int:
        nonlocal count           # modify the enclosing function's variable
        count += 1
        return count

    return inc


def scope_demo() -> None:
    print("UnboundLocalError caught:", broken_increment() == -1)
    c = make_counter()
    print("closure counter:", c(), c(), c())

    # Late-binding closure trap
    bad = [lambda: i for i in range(3)]
    good = [lambda i=i: i for i in range(3)]       # bind value NOW via default arg
    print("bad:", [f() for f in bad], "good:", [f() for f in good])


# ------------------------------------------------------------- 3. exceptions
class RetryError(Exception):
    """Raised when all retry attempts fail."""


def retry(fn: Callable[[], int], attempts: int = 3, delay: float = 0.0) -> int:
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except (ConnectionError, TimeoutError) as exc:   # specific, transient errors only
            last_exc = exc
            logger.warning("attempt %d/%d failed: %s", attempt, attempts, exc)
            time.sleep(delay)
    raise RetryError(f"failed after {attempts} attempts") from last_exc


def exceptions_demo() -> None:
    # try / except / else / finally
    for raw in ("42", "abc"):
        try:
            value = int(raw)
        except ValueError:
            print(f"{raw!r}: not a number")
        else:                                  # runs only if no exception
            print(f"{raw!r}: parsed {value}")
        finally:                               # always runs
            pass

    calls = {"n": 0}

    def flaky() -> int:
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("network down")
        return 200

    print("retry result:", retry(flaky))

    try:
        retry(lambda: (_ for _ in ()).throw(TimeoutError("slow")), attempts=2)
    except RetryError as exc:
        print("RetryError:", exc, "| cause:", repr(exc.__cause__))


# ------------------------------------------------------- 4. context managers
class Timer:
    """Class-based context manager."""

    def __enter__(self) -> Timer:
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.elapsed = time.perf_counter() - self.start
        return False                           # False = do NOT swallow exceptions


@contextmanager
def opened(name: str) -> Iterator[dict[str, str]]:
    """Generator-based context manager: setup, yield, cleanup."""
    resource = {"name": name, "state": "open"}
    print(f"  open {name}")
    try:
        yield resource
    finally:                                   # cleanup runs even on error
        resource["state"] = "closed"
        print(f"  close {name}")


def context_demo() -> None:
    with Timer() as t:
        sum(range(100_000))
    print("timer ran:", t.elapsed >= 0)

    try:
        with opened("db") as res:
            print("  using", res["name"])
            raise RuntimeError("boom")
    except RuntimeError:
        print("  error handled; resource cleaned up")

    with suppress(FileNotFoundError):          # intentionally ignore ONE specific error
        open("does-not-exist.txt").close()


# ------------------------------------------------------- 5. failure modes
def failure_modes_demo() -> None:
    # Mutating a list while iterating skips items
    nums = [2, 4, 6, 1]
    for n in nums:
        if n % 2 == 0:
            nums.remove(n)
    print("buggy remove:", nums, "(expected [1])")
    print("correct:", [n for n in [2, 4, 6, 1] if n % 2 != 0])

    # Float equality
    print("0.1 + 0.2 == 0.3:", 0.1 + 0.2 == 0.3)
    import math
    print("math.isclose:", math.isclose(0.1 + 0.2, 0.3))

    # == vs is
    x, y = [1, 2], [1, 2]
    print("== :", x == y, "| is:", x is y)

    # Common exceptions and what causes them
    cases: list[tuple[str, Callable[[], object]]] = [
        ("KeyError", lambda: {}["missing"]),
        ("IndexError", lambda: [][0]),
        ("AttributeError", lambda: None.upper()),     # type: ignore[attr-defined]
        ("TypeError", lambda: "a" + 1),               # type: ignore[operator]
        ("ValueError", lambda: int("x")),
        ("ZeroDivisionError", lambda: 1 / 0),
    ]
    for name, fn in cases:
        try:
            fn()
        except Exception as exc:
            print(f"  {name:18} -> {type(exc).__name__}: {exc}")

    # Shadowing a builtin
    def uses_shadowed_builtin() -> list[str]:
        list = ["a", "b"]                             # noqa: A001  (hides the builtin!)
        return list("xyz")                            # type: ignore[operator]

    try:
        uses_shadowed_builtin()
    except TypeError as exc:
        print("shadowed builtin:", exc)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)          # hide expected retry warnings
    for demo in (references_demo, scope_demo, exceptions_demo, context_demo, failure_modes_demo):
        print(f"\n--- {demo.__name__} ---")
        demo()
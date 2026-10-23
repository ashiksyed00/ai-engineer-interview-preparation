# Python · Mutability, Scope & Failure Modes

> **Goal:** Understand references, mutability, scope, exceptions, and context managers well enough to predict (and avoid) Python's most common bugs.

Runnable demo of everything below: [`examples.py`](./examples.py)

```bash
python examples.py
```

## Contents

1. [Names, references & mutability](#1-names-references--mutability)
2. [Scope: the LEGB rule](#2-scope-the-legb-rule)
3. [Exceptions](#3-exceptions)
4. [Context managers](#4-context-managers)
5. [Common failure modes](#5-common-failure-modes)
6. [Exercise](#6-exercise)
7. [Self-check](#7-self-check)

---

## 1. Names, references & mutability

In Python, a variable is a **name pointing to an object**, not a box holding a value. Assignment never copies.

```python
a = [1, 2, 3]
b = a            # b is another name for the SAME list
b.append(4)
print(a)         # [1, 2, 3, 4]
a is b           # True  (identity: same object)
```

| Mutable (can change in place) | Immutable (can't change) |
|-------------------------------|--------------------------|
| `list`, `dict`, `set`, `bytearray`, most custom objects | `int`, `float`, `bool`, `str`, `tuple`, `frozenset`, `bytes` |

```python
s = "hi"
t = s
t += "!"         # creates a NEW string; s is unchanged
print(s, t)      # hi hi!
```

**`==` vs `is`**
- `==` : do they have equal **values**?
- `is` : are they the **same object**? Use it for `None` only: `if x is None`.

```python
[1, 2] == [1, 2]   # True
[1, 2] is [1, 2]   # False
```

### Passing arguments

Python passes **references to objects** ("pass by assignment"):

```python
def add_item(items):
    items.append(99)       # MUTATES the caller's list

def rebind(items):
    items = [0]            # rebinds the local name only; caller unaffected
```

**Habit:** don't mutate arguments unless the function name makes that obvious (`append_to`, `sort_inplace`). Return a new object instead.

### Copying

```python
import copy
b = a.copy()              # shallow copy (also list(a), a[:])
c = copy.deepcopy(a)      # deep copy: nested objects copied too
```

### The mutable default argument trap

```python
def add(x, bucket=[]):    # BAD: one list, created once at definition time
    bucket.append(x)
    return bucket

def add(x, bucket=None):  # GOOD
    bucket = [] if bucket is None else bucket
    return [*bucket, x]
```

> More on copies and nested lists in [data-structures](../data-structures/README.md).

---

## 2. Scope: the LEGB rule

Python looks up a name in this order: **L**ocal → **E**nclosing function → **G**lobal (module) → **B**uilt-in.

```python
x = "global"

def outer():
    x = "enclosing"
    def inner():
        x = "local"
        print(x)       # local
    inner()
```

### Assigning makes a name local

```python
counter = 0

def inc():
    counter += 1       # UnboundLocalError! `+=` assigns, so counter is local here
```

Fixes (in order of preference):

```python
# 1. Pass in and return (best)
def inc(counter: int) -> int:
    return counter + 1

# 2. nonlocal: modify a variable in an enclosing function
def make_counter():
    count = 0
    def inc():
        nonlocal count
        count += 1
        return count
    return inc

# 3. global: modify a module-level variable (avoid; hard to test)
def inc():
    global counter
    counter += 1
```

Note: you can **read** globals freely and **mutate** a global list/dict without `global`. `global`/`nonlocal` are only needed to **rebind** a name.

### Closure late-binding trap

```python
funcs = [lambda: i for i in range(3)]
[f() for f in funcs]               # [2, 2, 2]  (all see the final i)

funcs = [lambda i=i: i for i in range(3)]
[f() for f in funcs]               # [0, 1, 2]  (value captured now)
```

### Other scope rules
- Loop variables **leak**: `for i in range(3): ...` leaves `i` defined afterward.
- Comprehension variables do **not** leak.
- Don't shadow builtins (`list`, `dict`, `id`, `type`, `input`, `max`):

```python
list = ["a", "b"]
list("xyz")        # TypeError: 'list' object is not callable
```

---

## 3. Exceptions

### Structure

```python
try:
    value = int(raw)
except ValueError:             # catch SPECIFIC errors
    print("not a number")
else:                          # runs only if NO exception
    print("parsed", value)
finally:                       # ALWAYS runs (cleanup)
    print("done")
```

### Hierarchy (simplified)

```
BaseException
├── KeyboardInterrupt, SystemExit      <- don't catch these
└── Exception                          <- base for normal errors
    ├── ValueError, TypeError
    ├── LookupError  (KeyError, IndexError)
    ├── OSError      (FileNotFoundError, ConnectionError, TimeoutError)
    └── your custom exceptions
```

### Rules

```python
# DON'T
try: ...
except: pass                    # hides everything, even Ctrl+C

# DO
try:
    data = load(path)
except FileNotFoundError:
    logger.error("missing file: %s", path)
    raise                       # re-raise if you can't really handle it
```

- Catch the **narrowest** exception you can handle; keep the `try` body small.
- **Chain** errors to keep the cause: `raise ConfigError("bad file") from exc`
- Use `logger.exception("msg")` inside `except` to log the full traceback.
- Define custom exceptions for your own failures: `class RetryError(Exception): ...`
- Python style is **EAFP** (try it, handle failure) over **LBYL** (check everything first).

### Retry pattern for flaky calls (APIs, networks)

```python
def retry(fn, attempts=3, delay=1.0):
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except (ConnectionError, TimeoutError) as exc:   # only transient errors
            last_exc = exc
            logger.warning("attempt %d/%d failed: %s", attempt, attempts, exc)
            time.sleep(delay * attempt)                  # simple backoff
    raise RetryError(f"failed after {attempts} attempts") from last_exc
```

Never retry errors that will never succeed (like `ValueError` from bad input).

---

## 4. Context managers

A context manager guarantees **setup and cleanup**, even when an error occurs. Use `with` for anything that must be released: files, locks, DB connections, network sessions, temp state.

```python
with open("data.txt") as f:       # file always closed
    text = f.read()
```

### Write your own

**Generator style** (easiest):

```python
from contextlib import contextmanager

@contextmanager
def opened(name):
    resource = connect(name)      # setup
    try:
        yield resource            # body of the `with` runs here
    finally:
        resource.close()          # cleanup, runs even on error
```

**Class style:**

```python
class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.elapsed = time.perf_counter() - self.start
        return False              # False = don't swallow exceptions
```

```python
with Timer() as t:
    do_work()
print(t.elapsed)
```

### Handy ones from the standard library

```python
from contextlib import suppress
import tempfile

with suppress(FileNotFoundError):       # deliberately ignore ONE specific error
    os.remove("cache.tmp")

with tempfile.TemporaryDirectory() as tmp:   # auto-deleted folder
    ...
```

Also: `threading.Lock()`, `unittest.mock.patch(...)`, and `httpx.Client()` all work as context managers.

---

## 5. Common failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Data changes "by itself" | Aliasing: two names, one mutable object | `.copy()` / `deepcopy`, or don't mutate |
| Default arg keeps old values | Mutable default argument | Use `None` sentinel |
| Items skipped in a loop | Modifying a list while iterating it | Build a new list with a comprehension |
| `UnboundLocalError` | Assigned to a global name inside a function | Pass in/return, or `global`/`nonlocal` |
| All lambdas return the same value | Late-binding closure | `lambda i=i: i` |
| `AttributeError: 'NoneType'...` | Function returned `None` (or forgot `return`) | Handle `None`; use type hints + mypy |
| `KeyError` | Missing dict key | `.get()`, `defaultdict`, or `in` check |
| `IndexError` | Index past the end | Check length, or iterate directly |
| `TypeError: 'X' not callable` | Shadowed a builtin | Rename the variable |
| `0.1 + 0.2 != 0.3` | Floating-point rounding | `math.isclose(a, b)` or `decimal.Decimal` |
| Slow string building | `s += x` in a big loop | `"".join(parts)` |
| Resource leaks (open files/connections) | Not closing on error | Use `with` |
| Errors vanish silently | Bare `except: pass` | Catch specific exceptions, log them |
| `RecursionError` | Missing base case or too-deep recursion | Add base case, or loop instead |
| `ImportError` from circular imports | Two modules import each other | Move shared code to a third module |

### Debugging toolkit

```python
print(type(x), repr(x), id(x))          # what exactly is this object?
import pdb; pdb.set_trace()             # or just: breakpoint()
```

```bash
python -m pdb script.py                 # run under the debugger
python -X dev script.py                 # extra runtime warnings
```

Read tracebacks **bottom-up**: the last line is the error, the lines above show how you got there.

---

## 6. Exercise

Create `exercises.py` in this folder:

1. **Predict, then run:**

```python
def f(x, acc=[]):
    acc.append(x)
    return acc

print(f(1), f(2))

a = [[0]] * 3
a[0].append(1)
print(a)

fs = [lambda: n for n in range(3)]
print([g() for g in fs])
```

2. Fix `f` so that each call gets its own list.
3. Write `remove_evens(nums)` that returns a new list and does not mutate the input. Test it with `[2, 4, 6, 1]`.
4. Write a `@contextmanager` called `temp_change_dir(path)` that `chdir`s into `path` and **always** restores the old directory.
5. Write `safe_int(raw: str, default: int = 0) -> int` that catches only `ValueError`, and logs a warning.
6. Write a `retry` decorator or helper that retries only `ConnectionError`, then raises a custom error `from` the original.

---

## 7. Self-check

- [ ] I can explain why `b = a` doesn't copy a list
- [ ] I know which built-in types are mutable and which are immutable
- [ ] I use `is` only for `None`, and `==` for values
- [ ] I never use mutable default arguments
- [ ] I can explain LEGB and why `counter += 1` fails inside a function
- [ ] I know the late-binding closure trap and its fix
- [ ] I catch specific exceptions, never bare `except:`, and chain with `raise ... from`
- [ ] I use `with` for files and any resource needing cleanup, and can write my own context manager
- [ ] I can recognise the common failure modes from their symptoms
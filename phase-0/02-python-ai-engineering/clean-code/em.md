# Python · Clean, Idiomatic Python

> **Goal:** Write Python that others can read at a glance, using functions, classes, modules, comprehensions, exceptions, and the standard library.

Runnable demo of everything below: [`examples.py`](./examples.py)

```bash
python examples.py
```

## Contents

1. [What "clean" means](#1-what-clean-means)
2. [Functions](#2-functions)
3. [Classes](#3-classes)
4. [Modules & project layout](#4-modules--project-layout)
5. [Comprehensions & generators](#5-comprehensions--generators)
6. [Exceptions](#6-exceptions)
7. [Standard-library toolbox](#7-standard-library-toolbox)
8. [Tooling: format, lint, type-check](#8-tooling-format-lint-type-check)
9. [Exercise](#9-exercise)
10. [Self-check](#10-self-check)

---

## 1. What "clean" means

- **Readable > clever.** Code is read far more than it is written.
- **Explicit names** (`user_count`, not `uc`). Naming rules from PEP 8:

| Thing | Style | Example |
|-------|-------|---------|
| variables, functions, modules | `snake_case` | `load_config` |
| classes | `PascalCase` | `ChatClient` |
| constants | `UPPER_SNAKE` | `MAX_RETRIES` |
| "private" | leading `_` | `_helper` |

- **Do one thing per function.** If you need "and" to describe it, split it.
- **Flat is better than nested.** Use early returns.

```python
# Nested
def get_discount(user):
    if user is not None:
        if user.is_active:
            return 0.1
    return 0.0

# Flat (guard clauses)
def get_discount(user):
    if user is None or not user.is_active:
        return 0.0
    return 0.1
```

---

## 2. Functions

```python
def chunk(items: list[str], size: int = 2) -> list[list[str]]:
    """Split items into chunks of `size`."""   # docstring: what, not how
    if size < 1:
        raise ValueError("size must be >= 1")
    return [items[i : i + size] for i in range(0, len(items), size)]
```

**Rules**
- Add **type hints** and a short **docstring**.
- Prefer **returning** values over printing or mutating arguments.
- Use keyword args for clarity: `connect(host="x", timeout=5)`.
- Keep functions short (roughly < 20 lines).

**Classic trap: mutable default arguments**

```python
def add_tag(tag, tags=[]):        # BAD: the list is shared across calls
    tags.append(tag)
    return tags

def add_tag(tag, tags=None):      # GOOD
    tags = [] if tags is None else tags
    return [*tags, tag]
```

**Handy idioms**

```python
a, b = b, a                              # swap
first, *rest = [1, 2, 3, 4]              # unpacking
for i, item in enumerate(items, start=1):  # index + item
for x, y in zip(xs, ys):                 # parallel loop
name = user.get("name", "unknown")       # dict default
if items:                                # truthiness, not len(items) > 0
f"{name} has {count:,} items"            # f-strings
```

---

## 3. Classes

Use a class when data and behavior belong together. For simple data holders, use a **dataclass**.

```python
from dataclasses import dataclass, field
from enum import Enum

class Role(Enum):
    USER = "user"
    ASSISTANT = "assistant"

@dataclass
class Message:
    role: Role
    content: str
    tags: list[str] = field(default_factory=list)   # safe mutable default

    @property
    def is_empty(self) -> bool:
        return not self.content.strip()
```

Gives you `__init__`, `__repr__`, and `__eq__` for free. Add `frozen=True` for immutability.

**Rules**
- Don't write a class when a function will do.
- `@property` for computed attributes, `@staticmethod`/`@classmethod` sparingly.
- Prefer **composition** over deep inheritance.
- Use `Enum` instead of "magic strings".

---

## 4. Modules & project layout

A module is a `.py` file. A package is a folder with modules (add `__init__.py`).

```
my_project/
├── src/my_project/
│   ├── __init__.py
│   ├── config.py
│   └── client.py
├── tests/
│   └── test_client.py
├── .gitignore
├── pyproject.toml
└── README.md
```

```python
# import order: standard library, third-party, local (ruff/isort does this for you)
import json
from pathlib import Path

import requests

from my_project.config import load_config
```

**Always guard script entry points:**

```python
def main() -> None:
    ...

if __name__ == "__main__":   # runs only when executed directly, not on import
    main()
```

Avoid `from x import *`. Avoid circular imports (move shared code to a third module).

---

## 5. Comprehensions & generators

```python
squares  = [x * x for x in range(10)]                  # list
evens    = [x for x in nums if x % 2 == 0]             # with filter
lengths  = {w: len(w) for w in words}                  # dict
unique   = {w.lower() for w in words}                  # set
total    = sum(x * x for x in range(10))               # generator expression (lazy)
```

**Generators** produce items lazily, which is ideal for big files or streams:

```python
def read_lines(path):
    with open(path) as f:
        for line in f:
            yield line.strip()
```

**Rule:** if a comprehension needs more than one `for` plus an `if`, or becomes hard to read, use a normal loop.

---

## 6. Exceptions

```python
class ConfigError(Exception):
    """Raised when the config is missing or invalid."""

def load_config(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise ConfigError(f"Config not found: {path}") from exc   # keep the cause
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {path}") from exc
```

**Rules**
- Catch **specific** exceptions. Never a bare `except:`; avoid `except Exception: pass`.
- Keep the `try` block small.
- Use `raise ... from exc` to preserve the original error.
- Use `else` (no error happened) and `finally` (always runs) when needed.
- Use **context managers** for cleanup:

```python
with open("data.txt") as f:      # file closes automatically, even on error
    data = f.read()
```

- Python style is EAFP ("easier to ask forgiveness than permission"): try it and handle the failure, rather than pre-checking everything.

---

## 7. Standard-library toolbox

Reach for these before installing a package.

| Need | Use |
|------|-----|
| File paths | `pathlib.Path` (not string concatenation) |
| Count things | `collections.Counter` |
| Group things | `collections.defaultdict` |
| Simple data class | `dataclasses.dataclass` |
| Fixed choices | `enum.Enum` |
| Cache results | `functools.lru_cache` |
| Loop helpers | `itertools` (`islice`, `chain`, `groupby`) |
| JSON | `json` |
| Dates/times | `datetime` |
| Logging (not `print`) | `logging` |
| CLI args | `argparse` |
| Type hints | `typing`, `collections.abc` |

```python
from pathlib import Path
from collections import Counter
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

Path("data").mkdir(exist_ok=True)
text = Path("data/notes.txt").read_text()
Counter(text.split()).most_common(3)

@lru_cache(maxsize=None)
def fib(n: int) -> int:
    return n if n < 2 else fib(n - 1) + fib(n - 2)

logger.info("loaded %d rows", 100)   # lazy formatting, use %s style in logging
```

---

## 8. Tooling: format, lint, type-check

Let tools enforce style so reviews focus on logic.

```bash
pip install ruff mypy

ruff format .          # auto-format (Black-compatible)
ruff check . --fix     # lint + auto-fix (unused imports, import order, etc.)
mypy .                 # check type hints
```

Optional `pyproject.toml` config:

```toml
[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]   # pycodestyle, pyflakes, isort, bugbear, pyupgrade
```

Commit these tools into your workflow from [Lesson 1](../../01-git-and-collaboration/README.md): run them before every commit (a pre-commit hook or CI check makes this automatic).

---

## 9. Exercise

Create `wordstats.py` in this folder:

1. `load_text(path: Path) -> str` raises a custom `InputError` if the file is missing.
2. `top_words(text: str, n: int = 5) -> list[tuple[str, int]]` uses `Counter` and a comprehension to ignore words shorter than 3 letters.
3. A `@dataclass` `Report` holding `total_words` and `top`.
4. `main()` with an `if __name__ == "__main__":` guard that uses `argparse` to take a file path and logs the result.
5. Run `ruff format . && ruff check . && mypy .` until clean.
6. Commit on a branch and open a PR.

---

## 10. Self-check

- [ ] My functions have type hints, docstrings, and do one thing
- [ ] I never use mutable default arguments
- [ ] I use dataclasses/enums instead of loose dicts and magic strings
- [ ] Scripts have a `main()` and an `if __name__ == "__main__":` guard
- [ ] I choose comprehensions for simple transforms and loops for complex ones
- [ ] I catch specific exceptions and use `raise ... from`
- [ ] I use `pathlib`, `logging`, `Counter`, `defaultdict` instead of reinventing them
- [ ] `ruff` and `mypy` pass cleanly on my code

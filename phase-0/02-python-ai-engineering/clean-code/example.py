"""Runnable examples for clean, idiomatic Python.

Run:  python examples.py
"""

from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from itertools import islice
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------- functions
def chunk(items: list[str], size: int = 2) -> list[list[str]]:
    """Split items into chunks of `size` (last chunk may be smaller)."""
    if size < 1:
        raise ValueError("size must be >= 1")
    return [items[i : i + size] for i in range(0, len(items), size)]


def add_tag(tag: str, tags: list[str] | None = None) -> list[str]:
    """Avoid mutable default args: use None, then create inside."""
    tags = [] if tags is None else tags
    return [*tags, tag]  # return a new list, don't mutate the input


# ------------------------------------------------------------------ classes
class Role(Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    role: Role
    content: str
    tokens: int = 0
    tags: list[str] = field(default_factory=list)  # safe mutable default

    def __post_init__(self) -> None:
        self.tokens = len(self.content.split())

    @property
    def is_empty(self) -> bool:
        return not self.content.strip()


# --------------------------------------------------------------- exceptions
class ConfigError(Exception):
    """Raised when the config file is missing or invalid."""


def load_config(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise ConfigError(f"Config not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {path}") from exc


# ------------------------------------------------------------ stdlib helpers
@lru_cache(maxsize=None)
def fib(n: int) -> int:
    return n if n < 2 else fib(n - 1) + fib(n - 2)


def first_n_squares(n: int):
    """Generator: lazy, memory-friendly."""
    return islice((x * x for x in range(10**9)), n)


# --------------------------------------------------------------------- main
def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print(chunk(["a", "b", "c", "d", "e"], 2))
    print(add_tag("x"), add_tag("y"))  # independent lists, no shared state

    msg = Message(Role.USER, "hello there AI engineer")
    print(msg, msg.is_empty)

    # comprehensions
    words = ["apple", "bob", "cat", "apple", "dog", "bob", "apple"]
    lengths = {w: len(w) for w in set(words)}  # dict comp
    long_words = [w for w in words if len(w) > 3]  # list comp
    print(sorted(lengths.items()), long_words)

    # collections
    print(Counter(words).most_common(2))
    groups: defaultdict[int, list[str]] = defaultdict(list)
    for w in words:
        groups[len(w)].append(w)
    print(dict(groups))

    # unpacking, enumerate, zip
    for i, (a, b) in enumerate(zip("abc", [1, 2, 3]), start=1):
        print(i, a, b)

    # exceptions
    try:
        load_config(Path("missing.json"))
    except ConfigError as err:
        logger.warning("Handled: %s", err)

    print(fib(30), list(first_n_squares(5)))


if __name__ == "__main__":
    main()
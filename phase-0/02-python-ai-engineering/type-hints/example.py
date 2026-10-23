"""Runnable examples for type hints and typed models (standard library only).

Run:    python examples.py
Check:  mypy examples.py
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import Literal, Protocol, TypedDict, TypeVar

T = TypeVar("T")


# ------------------------------------------------------------ basic hints
def greet(name: str, times: int = 1) -> str:
    return " ".join(f"Hello, {name}!" for _ in range(times))


def average(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def first(items: Sequence[T], default: T) -> T:
    """Generic: return type matches the element type."""
    return items[0] if items else default


def apply_all(fn: Callable[[int], int], values: Iterable[int]) -> list[int]:
    return [fn(v) for v in values]


# ------------------------------------------------- Optional + type narrowing
def find_user(user_id: int, db: dict[int, str]) -> str | None:
    return db.get(user_id)


def shout_user(user_id: int, db: dict[int, str]) -> str:
    name = find_user(user_id, db)
    if name is None:                 # mypy forces you to handle None here
        return "unknown"
    return name.upper()              # narrowed to str


# ---------------------------------------------------------------- Literal
Role = Literal["system", "user", "assistant"]


def make_message(role: Role, content: str) -> dict[str, str]:
    return {"role": role, "content": content}
    # make_message("admin", "hi")  -> mypy error: not a valid Role


# -------------------------------------------------------------- TypedDict
class ChatMessage(TypedDict):
    role: Role
    content: str


def last_content(history: list[ChatMessage]) -> str:
    return history[-1]["content"]    # mypy knows this key exists and is a str


# ---------------------------------------------------------------- Protocol
class Embedder(Protocol):
    """Structural typing: anything with a matching embed() fits. No inheritance."""

    def embed(self, text: str) -> list[float]: ...


class FakeEmbedder:
    def embed(self, text: str) -> list[float]:
        return [float(len(text)), 0.0]


def embed_all(embedder: Embedder, texts: list[str]) -> list[list[float]]:
    return [embedder.embed(t) for t in texts]


# ------------------------------------------------------- dataclass models
@dataclass(frozen=True)
class Document:
    id: str
    text: str
    tags: list[str] = field(default_factory=list)
    score: float = 0.0

    def __post_init__(self) -> None:
        # dataclasses do NOT validate types at runtime; add checks yourself
        if not self.text.strip():
            raise ValueError("text must not be empty")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0 and 1")


# --------------------------------------------------------------------- main
def main() -> None:
    print(greet("Ada", 2))
    print(average([1, 2, 3]), first([], "fallback"), apply_all(lambda x: x * 2, [1, 2]))
    print(shout_user(1, {1: "ada"}), shout_user(2, {}))
    print(make_message("user", "hi"))
    print(last_content([{"role": "user", "content": "hello"}]))
    print(embed_all(FakeEmbedder(), ["abc", "de"]))

    doc = Document(id="1", text="hello", tags=["a"], score=0.5)
    print(doc)

    # Hints are NOT enforced at runtime: this runs fine, but mypy would flag it
    print(greet(123))                # type: ignore[arg-type]

    try:
        Document(id="2", text="  ", score=0.5)
    except ValueError as exc:
        print("Validation failed:", exc)


if __name__ == "__main__":
    main()
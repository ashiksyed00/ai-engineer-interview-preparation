# Python · Type Hints & Typed Models

> **Goal:** Use type hints, dataclass/Pydantic-style models, and static analysis to make interfaces explicit and catch mistakes before they run.

Files in this folder:
- [`examples.py`](./examples.py): type hints, `TypedDict`, `Protocol`, dataclasses (standard library only)
- [`pydantic_example.py`](./pydantic_example.py): validated models with Pydantic v2

```bash
python examples.py

pip install pydantic mypy
python pydantic_example.py
mypy examples.py
```

## Contents

1. [Why type hints?](#1-why-type-hints)
2. [Basic hints](#2-basic-hints)
3. [Optional, unions & narrowing](#3-optional-unions--narrowing)
4. [Useful typing tools](#4-useful-typing-tools)
5. [Typed models: dataclass vs. TypedDict vs. Pydantic](#5-typed-models-dataclass-vs-typeddict-vs-pydantic)
6. [Pydantic essentials](#6-pydantic-essentials)
7. [Static analysis with mypy](#7-static-analysis-with-mypy)
8. [Exercise](#8-exercise)
9. [Self-check](#9-self-check)

---

## 1. Why type hints?

- They document what a function takes and returns, so you don't have to guess.
- Editors give better autocomplete and catch errors as you type.
- `mypy` finds bugs (wrong types, forgotten `None` checks) **before** you run the code.
- **Important:** Python does **not** enforce hints at runtime. They are checked by tools, not the interpreter.

```python
def greet(name: str) -> str:
    return f"Hello, {name}"

greet(123)   # runs fine! mypy flags it: Argument 1 has incompatible type "int"
```

---

## 2. Basic hints

```python
name: str = "Ada"
count: int = 0
price: float = 9.99
active: bool = True

# Collections (Python 3.9+: use built-in generics, no need for typing.List)
names: list[str] = []
scores: dict[str, float] = {}
point: tuple[float, float] = (1.0, 2.0)       # fixed length
values: tuple[int, ...] = (1, 2, 3)           # any length
unique: set[int] = set()

# Functions
def add(a: int, b: int = 0) -> int:
    return a + b

def log(msg: str) -> None:        # returns nothing
    print(msg)
```

**Prefer abstract types for parameters, concrete types for return values:**

```python
from collections.abc import Sequence, Iterable, Mapping, Callable

def average(values: Sequence[float]) -> float: ...    # accepts list, tuple, ...
def total(items: Iterable[int]) -> int: ...           # accepts anything loopable
def apply(fn: Callable[[int], int], x: int) -> int: ...
```

---

## 3. Optional, unions & narrowing

```python
def find_user(user_id: int) -> str | None:     # "str or None" (3.10+ syntax)
    ...

name = find_user(1)
name.upper()            # mypy error: name might be None

if name is None:        # "narrowing": after this check, mypy knows it's a str
    return "unknown"
return name.upper()
```

This catches the classic `AttributeError: 'NoneType' object has no attribute ...` at check time instead of in production.

```python
def parse(value: int | str) -> int:
    if isinstance(value, str):     # narrowing with isinstance
        return int(value)
    return value
```

---

## 4. Useful typing tools

```python
from typing import Literal, TypedDict, Protocol, TypeVar, Any
```

**`Literal`**: restrict to specific values (instead of "magic strings")

```python
Role = Literal["system", "user", "assistant"]
def send(role: Role, text: str) -> None: ...
send("admin", "hi")      # mypy error
```

**`TypedDict`**: describe the shape of a dict (great for JSON-like data)

```python
class ChatMessage(TypedDict):
    role: Role
    content: str

msg: ChatMessage = {"role": "user", "content": "hi"}
```

**`Protocol`**: "anything with these methods" (duck typing, checked statically)

```python
class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...

def run(e: Embedder) -> None: ...   # any class with embed() works, no inheritance needed
```

**`TypeVar`**: generics, where input and output types are linked

```python
T = TypeVar("T")
def first(items: Sequence[T], default: T) -> T: ...
```

**`Any`**: opt out of checking. Use sparingly; it hides bugs.

---

## 5. Typed models: dataclass vs. TypedDict vs. Pydantic

| | `TypedDict` | `@dataclass` | Pydantic `BaseModel` |
|---|:---:|:---:|:---:|
| It is a... | plain `dict` | normal class | validated class |
| Runtime type checking | No | **No** | **Yes** |
| Converts/coerces data | No | No | Yes (`"5"` → `5`) |
| Parses JSON | No | No | Yes |
| Extra install | No | No | `pip install pydantic` |
| Best for | typing existing dicts/JSON | internal data containers | **external/untrusted data** (APIs, configs, LLM output) |

**Rule of thumb:** use dataclasses for trusted internal data, Pydantic at the **boundaries** where data enters your system (HTTP requests, files, environment variables, LLM responses).

Dataclass example (note it does **not** validate types):

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)          # frozen = immutable
class Document:
    id: str
    text: str
    tags: list[str] = field(default_factory=list)
    score: float = 0.0

    def __post_init__(self) -> None:         # add your own validation
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0 and 1")

Document(id=1, text="x")   # runs! id is an int, but nothing checks it at runtime
```

---

## 6. Pydantic essentials

```python
from typing import Literal
from pydantic import BaseModel, Field, ValidationError, field_validator

class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)

class ChatRequest(BaseModel):
    model: str = "demo-model"
    messages: list[Message] = Field(min_length=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)

    @field_validator("model")
    @classmethod
    def model_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("model must not be blank")
        return v.strip()
```

```python
# Validate from a dict or from a JSON string
req = ChatRequest.model_validate({"messages": [{"role": "user", "content": "hi"}]})
req = ChatRequest.model_validate_json('{"messages": [{"role": "user", "content": "hi"}]}')

# Invalid input raises a structured error
try:
    ChatRequest.model_validate({"messages": [], "temperature": 5})
except ValidationError as exc:
    print(exc.errors())

# Convert back out
req.model_dump()                       # -> dict
req.model_dump_json(exclude_none=True) # -> JSON string
```

**Why this matters for AI engineering:**
- **FastAPI** uses Pydantic models for request/response validation (coming later in the roadmap).
- Parse and validate **structured LLM output** (JSON) before trusting it.
- Pydantic can also load typed settings from environment variables (via the `pydantic-settings` package).

> Pydantic v2 method names: `model_validate`, `model_dump`. Older v1 tutorials use `parse_obj` and `.dict()`, which are deprecated.

---

## 7. Static analysis with mypy

```bash
pip install mypy
mypy .                    # check everything
mypy --strict src/        # strictest mode (aim for this on new code)
```

Optional `pyproject.toml` config:

```toml
[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true     # for libraries without type info
```

**Reading common errors**

| Error | Meaning |
|-------|---------|
| `Argument 1 has incompatible type "int"; expected "str"` | wrong argument type |
| `Item "None" of "str \| None" has no attribute "upper"` | forgot to handle `None` |
| `Missing return statement` | a code path returns nothing |
| `Function is missing a type annotation` | (strict mode) add hints |

**Silencing a false positive** (last resort, add the specific code):

```python
value = something()  # type: ignore[arg-type]
```

**Add it to your workflow:** run `ruff check . && mypy .` before each commit, and in CI so PRs can't merge with type errors (see [Lesson 1](../../01-git-and-collaboration/README.md) on protected branches).

---

## 8. Exercise

Create `exercises.py` in this folder:

1. Add full type hints to this function, then fix the bug mypy reports:

```python
def get_initial(name):
    return name[0].upper() if name else None

print(get_initial("ada").lower())
```

2. Define `Role = Literal[...]` and a `TypedDict` called `ChatMessage`.
3. Write a `@dataclass(frozen=True)` called `Document` with a `__post_init__` check.
4. Write a Pydantic `ChatRequest` model with `temperature` limited to 0-2.
5. Feed it bad data (`temperature=5`, empty `messages`) and print the errors.
6. Define a `Protocol` called `Retriever` with `search(query: str, k: int) -> list[str]`, and write two small classes that satisfy it.
7. Run `mypy --strict exercises.py` until it is clean.

---

## 9. Self-check

- [ ] I know hints are checked by tools (mypy/IDE), not enforced at runtime
- [ ] I use `list[str]`, `dict[str, int]`, and `X | None` syntax
- [ ] I handle `None` explicitly instead of ignoring it
- [ ] I use `Literal` instead of magic strings
- [ ] I know when to pick `TypedDict` vs. `dataclass` vs. Pydantic
- [ ] I use Pydantic at the boundaries where untrusted data comes in
- [ ] I can run `mypy` and understand its common errors
- [ ] I avoid `Any` and use `# type: ignore[code]` only as a last resort
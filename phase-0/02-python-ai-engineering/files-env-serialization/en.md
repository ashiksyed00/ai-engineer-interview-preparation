# Python · Files, Paths, Env Vars & Serialization

> **Goal:** Read and write files safely, build paths that work on any OS, load configuration from environment variables, and move data in and out of JSON, JSONL, and CSV.

Files in this folder:
- [`examples.py`](./examples.py): runnable demo (standard library only, works inside a temp folder)
- [`.env.example`](./.env.example): template for local configuration

```bash
python examples.py
```

## Contents

1. [Paths with `pathlib`](#1-paths-with-pathlib)
2. [Reading & writing files](#2-reading--writing-files)
3. [Environment variables & secrets](#3-environment-variables--secrets)
4. [JSON](#4-json)
5. [JSONL (JSON Lines)](#5-jsonl-json-lines)
6. [CSV](#6-csv)
7. [Serialization: what to use when](#7-serialization-what-to-use-when)
8. [Safety & failure modes](#8-safety--failure-modes)
9. [Exercise](#9-exercise)
10. [Self-check](#10-self-check)

---

## 1. Paths with `pathlib`

Use `pathlib.Path`, not string concatenation. It handles `/` vs `\` for you.

```python
from pathlib import Path

root = Path("data")
f = root / "raw" / "notes.txt"        # build with /

f.name        # 'notes.txt'
f.stem        # 'notes'
f.suffix      # '.txt'
f.parent      # Path('data/raw')
f.exists(); f.is_file(); f.is_dir()

root.mkdir(parents=True, exist_ok=True)     # create folders, no error if present
list(root.glob("*.csv"))                    # files in this folder
list(root.rglob("*.csv"))                   # recursive
f.with_suffix(".md")                        # change extension

Path.home()     # user's home folder
Path.cwd()      # current working directory
```

**Anchor paths to your script, not the working directory:**

```python
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"          # works no matter where you run python from
```

---

## 2. Reading & writing files

### Quick (small files)

```python
text = Path("notes.txt").read_text(encoding="utf-8")
Path("out.txt").write_text("hello\n", encoding="utf-8")
raw = Path("image.png").read_bytes()
```

### With `open()` (large files, appending)

```python
with open("notes.txt", encoding="utf-8") as f:     # always use `with`
    for line in f:                                 # lazy: one line at a time
        print(line.strip())

with open("log.txt", "a", encoding="utf-8") as f:  # append
    f.write("new line\n")
```

| Mode | Meaning |
|------|---------|
| `"r"` | read text (default) |
| `"w"` | write text, **erases existing content** |
| `"a"` | append |
| `"x"` | create, error if it already exists |
| `"rb"` / `"wb"` | binary read / write |

**Always pass `encoding="utf-8"`.** The default depends on the OS and causes "works on my machine" bugs.

### Atomic write (don't leave half-written files)

```python
def atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)      # rename is atomic on the same filesystem
```

### Other handy tools

```python
import shutil, tempfile

shutil.copy("a.txt", "b.txt")
shutil.rmtree("old_folder")                 # careful: deletes recursively
Path("x.txt").unlink(missing_ok=True)       # delete a file

with tempfile.TemporaryDirectory() as tmp:  # auto-cleaned scratch space (great for tests)
    ...
```

---

## 3. Environment variables & secrets

Config that changes between machines (API keys, URLs, flags) belongs in **environment variables**, not in code. This is how you keep secrets out of Git (see [Lesson 1](../../01-git-and-collaboration/README.md)).

```python
import os

api_key = os.environ["API_KEY"]                       # KeyError if missing: fail fast
timeout = int(os.environ.get("API_TIMEOUT", "30"))    # default + convert
debug   = os.environ.get("DEBUG", "false").lower() in {"1", "true", "yes"}
```

**Env vars are always strings.** `"false"` is truthy, so convert explicitly.

### Set them

```bash
# macOS / Linux
export API_KEY="sk-..."
API_KEY="sk-..." python app.py        # for one command only

# Windows PowerShell
$env:API_KEY = "sk-..."
```

### Use a `.env` file for local development

```bash
# .env  (git-ignored, real values)
API_KEY=sk-real-key
API_TIMEOUT=30
```

```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
import os

load_dotenv()                           # reads .env into os.environ
api_key = os.environ["API_KEY"]
```

**The pattern:**
1. Add `.env` to `.gitignore`.
2. Commit [`.env.example`](./.env.example) with placeholder values.
3. Document the variables in your README's *Configuration* section.
4. Never print or log secrets.

> For typed, validated settings, `pydantic-settings` loads env vars into a Pydantic model (see [type-hints](../type-hints/README.md)).

---

## 4. JSON

JSON maps to Python like this:

| JSON | Python |
|------|--------|
| object | `dict` |
| array | `list` |
| string / number | `str` / `int`, `float` |
| `true` / `false` / `null` | `True` / `False` / `None` |

```python
import json

data = {"name": "Ada", "tags": ["ml", "py"], "score": 0.9}

s = json.dumps(data, indent=2)          # dict -> string
d = json.loads(s)                       # string -> dict

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)        # dict -> file
with open("data.json", encoding="utf-8") as f:
    d = json.load(f)                    # file -> dict
```

Remember: `dumps`/`loads` = **s**tring, `dump`/`load` = **f**ile.

### Gotchas

```python
# 1. Non-ASCII text: keep it readable
json.dumps({"city": "Zürich"}, ensure_ascii=False)

# 2. Unsupported types (datetime, set, dataclass) raise TypeError
from dataclasses import asdict
json.dumps(asdict(record), default=str)      # fallback converter

# 3. Dict keys become strings, tuples/sets aren't allowed
json.loads(json.dumps({1: "a"}))             # {'1': 'a'}

# 4. Invalid JSON (single quotes, trailing commas) -> json.JSONDecodeError
try:
    json.loads(raw)
except json.JSONDecodeError as exc:
    ...
```

### Typed models in and out

```python
from pydantic import BaseModel

class Config(BaseModel):
    model: str
    temperature: float = 0.7

cfg = Config.model_validate_json(Path("config.json").read_text(encoding="utf-8"))
Path("config.json").write_text(cfg.model_dump_json(indent=2), encoding="utf-8")
```

---

## 5. JSONL (JSON Lines)

One JSON object per line. **The standard format for AI datasets, logs, and batch jobs.** It can be streamed and appended to without loading everything.

```jsonl
{"prompt": "hi", "label": 1}
{"prompt": "bye", "label": 0}
```

```python
def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

def read_jsonl(path):                       # generator: constant memory
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

# append one record (e.g. logging LLM calls)
with open("calls.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps({"prompt": "hi", "tokens": 12}) + "\n")
```

---

## 6. CSV

```python
import csv

# Write
with open("people.csv", "w", newline="", encoding="utf-8") as f:   # newline="" is required
    writer = csv.DictWriter(f, fieldnames=["name", "age"])
    writer.writeheader()
    writer.writerows([{"name": "Ada", "age": 36}, {"name": "Bob", "age": 25}])

# Read
with open("people.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        age = int(row["age"])          # CSV has no types: everything is a string
```

Use the `csv` module (not `line.split(",")`): it handles quotes, commas inside fields, and newlines.

> For analysis, `pandas.read_csv("people.csv")` is the usual next step (covered later in the roadmap).

---

## 7. Serialization: what to use when

| Format | Human-readable | Types preserved | Safe to load untrusted | Use for |
|--------|:-:|:-:|:-:|---------|
| **JSON** | Yes | Basic only | **Yes** | APIs, configs, small data |
| **JSONL** | Yes | Basic only | Yes | datasets, logs, streaming |
| **CSV** | Yes | **No** (all strings) | Yes | tabular data, spreadsheets |
| **TOML/YAML** | Yes | Basic | TOML yes; YAML use `safe_load` | configuration files |
| **pickle** | No | Any Python object | **NO** | trusted, temporary Python-only caching |
| **Parquet** | No | Yes | Yes | large analytics data (later) |

Rule of thumb: **default to JSON/JSONL.** Reach for pickle only for data you created yourself.

---

## 8. Safety & failure modes

| Problem | Cause | Fix |
|---------|-------|-----|
| `FileNotFoundError` | Wrong path / wrong working directory | Anchor on `Path(__file__).parent`; check `.exists()` |
| `UnicodeDecodeError` | Wrong or default encoding | `encoding="utf-8"` everywhere |
| Data silently erased | Opened with `"w"` instead of `"a"` | Double-check the mode |
| Blank lines in Windows CSVs | Forgot `newline=""` | Always pass it with `csv` |
| `JSONDecodeError` | Single quotes, trailing commas, empty file | Validate; catch and report the file name |
| `TypeError: not JSON serializable` | `datetime`, `set`, custom class | `default=str`, or convert first |
| Out of memory | `.read()` on a huge file | Iterate lines / use a generator |
| Leaked secret in Git | `.env` committed | `.gitignore`; rotate the key |
| Code execution risk | `pickle.load` / `yaml.load` on untrusted data | Use JSON, or `yaml.safe_load` |
| Path traversal (`../../etc/passwd`) | Using user input as a path | Resolve and verify it stays inside your base folder |

```python
# Path traversal guard
def safe_join(base: Path, user_path: str) -> Path:
    target = (base / user_path).resolve()
    if not target.is_relative_to(base.resolve()):     # Python 3.9+
        raise ValueError("path escapes base directory")
    return target
```

---

## 9. Exercise

Create `exercises.py` in this folder:

1. Write `load_settings()` that reads `API_KEY` (required) and `API_TIMEOUT` (int, default 30) from environment variables, raising a clear custom error if `API_KEY` is missing.
2. Create a `.env` from `.env.example`, load it with `python-dotenv`, and confirm `.env` does **not** show up in `git status` (add it to `.gitignore`).
3. Write `save_json(path, data)` using an atomic write, and `load_json(path, default=None)` that returns `default` if the file is missing and raises a helpful error if it contains invalid JSON.
4. Write 1,000 records to `data.jsonl` and process them with a generator, computing the average of a `score` field without ever holding all records in memory.
5. Convert `people.csv` to JSON, turning `age` into an `int`.
6. Serialize a `@dataclass` that contains a `datetime` to JSON and back (hint: `isoformat()` / `datetime.fromisoformat()`).
7. Stretch: write `safe_join` and test that `"../secret.txt"` is rejected.

---

## 10. Self-check

- [ ] I build paths with `pathlib` and anchor them with `Path(__file__)`
- [ ] I always use `with` and `encoding="utf-8"` when opening files
- [ ] I know the difference between modes `"w"`, `"a"`, and `"x"`
- [ ] I read config and secrets from env vars, and know they are always strings
- [ ] `.env` is git-ignored and `.env.example` is committed
- [ ] I know `dumps/loads` (strings) vs. `dump/load` (files)
- [ ] I can handle non-serializable types and `JSONDecodeError`
- [ ] I use JSONL and generators for large datasets
- [ ] I use the `csv` module with `newline=""` and remember all values are strings
- [ ] I know why `pickle` is unsafe for untrusted data
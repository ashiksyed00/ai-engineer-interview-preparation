# Python · Environments & Dependencies with uv

> **Goal:** Manage virtual environments and dependencies with `uv`, understand `pyproject.toml` and lockfiles, and make your project reproducible on any machine with two commands.

Files in this folder:
- [`pyproject.example.toml`](./pyproject.example.toml): annotated `pyproject.toml` you can copy

> **Verification note:** `uv init`, `uv run`, `uv lock`, `uv tree`, and `uv export` were run in a sandbox while writing these notes (uv 0.11.x), and the files they generate are shown as observed. Commands that download from PyPI (`uv add httpx`, `uvx ruff`, etc.) were **not** run (no network there), so their behavior is based on the [official uv docs](https://docs.astral.sh/uv/). Try them once on your machine.

## Contents

1. [Why environments & lockfiles?](#1-why-environments--lockfiles)
2. [Install uv](#2-install-uv)
3. [Quick start: a new project](#3-quick-start-a-new-project)
4. [`pyproject.toml` explained](#4-pyprojecttoml-explained)
5. [Everyday commands](#5-everyday-commands)
6. [Locking & reproducibility](#6-locking--reproducibility)
7. [Managing Python versions](#7-managing-python-versions)
8. [Running tools & one-off scripts](#8-running-tools--one-off-scripts)
9. [Git, CI & README integration](#9-git-ci--readme-integration)
10. [pip ↔ uv cheat sheet](#10-pip--uv-cheat-sheet)
11. [Common problems](#11-common-problems)
12. [Exercise](#12-exercise)
13. [Self-check](#13-self-check)

---

## 1. Why environments & lockfiles?

- **Virtual environment (venv):** an isolated folder of packages for **one project**, so project A's `pydantic 1.x` never collides with project B's `pydantic 2.x`. Never `pip install` into your system Python.
- **Dependency drift:** "works on my machine" usually means different package versions. Without pinning, `pip install requests` today and next year give different results.
- **Lockfile:** records the **exact** versions of every package (including transitive ones) so everyone gets an identical environment.

| File | Contains | Edited by | Committed? |
|------|----------|-----------|:----------:|
| `pyproject.toml` | what you **want** (broad ranges: `httpx>=0.27`) | you / `uv add` | **Yes** |
| `uv.lock` | what you **got** (exact versions, all platforms) | uv only (never by hand) | **Yes** |
| `.venv/` | the installed packages | uv | **No** (git-ignored) |
| `.python-version` | which Python to use | `uv python pin` | **Yes** |

`uv` is a fast, all-in-one tool (written in Rust) that replaces `pip`, `venv`, `pip-tools`, `pyenv`, and `pipx`.

---

## 2. Install uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# or via pip / Homebrew
pip install uv
brew install uv

uv --version
uv self update          # update (when installed with the standalone installer)
```

Check the [install page](https://docs.astral.sh/uv/getting-started/installation/) if a command has changed.

---

## 3. Quick start: a new project

```bash
uv init my-app              # creates folder, git repo, and starter files
cd my-app
```

What `uv init` creates (observed):

```
my-app/
├── .git/
├── .gitignore          # ignores .venv, __pycache__, build/, dist/ ...
├── .python-version     # e.g. 3.12
├── README.md
├── main.py
└── pyproject.toml
```

```bash
uv run main.py              # first run auto-creates .venv and uv.lock
# Using CPython 3.12.3 interpreter ...
# Creating virtual environment at: .venv
# Hello from my-app!
```

Now add dependencies:

```bash
uv add httpx pydantic          # runtime dependencies
uv add --dev pytest ruff mypy  # development-only tools
uv run pytest                  # run anything inside the project environment
```

Variants of `uv init`:

| Command | Use for |
|---------|---------|
| `uv init` | initialize in the **current** folder |
| `uv init my-app` | new app folder |
| `uv init --lib my-lib` | a reusable library (`src/` layout + build system) |
| `uv init --package my-app` | an app packaged with an installable entry point |
| `uv init --bare` | only a `pyproject.toml` |

> `uv init` doesn't ignore `.env`. **Add `.env` to `.gitignore` yourself** (see [Lesson 1](../../01-git-and-collaboration/README.md) and [files-env-serialization](../files-env-serialization/README.md)).

---

## 4. `pyproject.toml` explained

The standard config file for Python projects. See the full annotated version in [`pyproject.example.toml`](./pyproject.example.toml). What `uv init` generates (observed):

```toml
[project]
name = "my-app"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.12"
dependencies = []
```

After `uv add httpx` and `uv add --dev pytest`, it looks like this (the versions are whatever is current when you run it):

```toml
[project]
dependencies = ["httpx>=0.27"]

[dependency-groups]
dev = ["pytest>=8"]
```

| Section | Purpose |
|---------|---------|
| `[project]` | name, version, Python version, **runtime dependencies** |
| `[project.optional-dependencies]` | extras users can opt into: `pip install pkg[plot]` |
| `[dependency-groups]` | dev-only groups (`dev`, `docs`, `test`), never shipped to users |
| `[tool.*]` | settings for tools: `ruff`, `mypy`, `pytest`, `uv` |
| `[build-system]` | only for installable packages/libraries (added by `--lib`/`--package`) |

**Version specifiers:**

| Spec | Meaning |
|------|---------|
| `httpx>=0.27` | 0.27 or newer (the common default) |
| `httpx>=0.27,<1.0` | within a range |
| `httpx~=0.27.0` | compatible release (`>=0.27.0,<0.28`) |
| `httpx==0.27.2` | exact pin (use sparingly; the lockfile already pins) |

**Applications vs. libraries:** apps can use loose ranges plus a lockfile. Libraries that others install should avoid over-tight upper bounds.

---

## 5. Everyday commands

```bash
# Dependencies
uv add requests                 # add + update pyproject.toml + uv.lock + install
uv add 'httpx>=0.27,<1'         # with a version constraint
uv add --dev pytest             # dev group
uv add --group docs mkdocs      # custom group
uv remove requests              # remove

# Environment
uv sync                         # make .venv exactly match uv.lock
uv run python script.py         # run in the project env (no activation needed)
uv run pytest
uv tree                         # show the dependency tree

# Optional: activate manually (editors, Jupyter, etc.)
source .venv/bin/activate       # Windows: .venv\Scripts\activate
```

**`uv run` is the key habit.** Before every run, uv checks that the lockfile matches `pyproject.toml` and that `.venv` matches the lockfile, so you never need to remember to `pip install` again.

```bash
# Plain virtual environment, without a project (pip-style)
uv venv                         # creates .venv
uv pip install requests         # pip-compatible interface (not recorded in pyproject.toml)
```

Prefer `uv add` over `uv pip install` in projects: `uv add` records the dependency, and `uv pip install` does not.

---

## 6. Locking & reproducibility

```bash
uv lock                          # resolve and write uv.lock (without installing)
uv sync                          # install exactly what's in uv.lock
```

**Reproduce someone's environment:**

```bash
git clone <repo> && cd <repo>
uv sync                          # done: same versions as everyone else
uv run pytest
```

**Upgrading deliberately:**

```bash
uv lock --upgrade                         # upgrade everything within pyproject.toml's ranges
uv lock --upgrade-package httpx           # upgrade just one package
uv sync
```

Then run tests, and commit `pyproject.toml` + `uv.lock` **together** in one PR.

**Strict modes for CI and deployment:**

| Flag | Behavior |
|------|----------|
| `uv sync --locked` | **fails** if `uv.lock` is out of date with `pyproject.toml` (best for CI) |
| `uv sync --frozen` | install from `uv.lock` as-is, without checking it's up to date |
| `uv lock --check` | verify the lockfile is current (exit non-zero if not) |
| `uv sync --no-dev` | skip dev dependencies (production images) |

```bash
uv export --no-hashes > requirements.txt   # export for tools that need requirements.txt
```

`uv.lock` is **cross-platform**: one lockfile covers Linux, macOS, and Windows and multiple Python versions. It is human-readable TOML, but never edit it by hand.

> The lockfile pins **Python packages**, not system libraries or your OS. For full reproducibility beyond Python, use containers (Docker, a later lesson).

---

## 7. Managing Python versions

uv can download and manage Python itself, so you don't need `pyenv`.

```bash
uv python list                  # available/installed versions
uv python install 3.12          # download a Python
uv python pin 3.12              # write .python-version for this project
uv venv --python 3.12
```

`requires-python` in `pyproject.toml` says what is **allowed**; `.python-version` says what to **use locally**.

---

## 8. Running tools & one-off scripts

```bash
# Run a tool without installing it into your project (like npx)
uvx ruff check .
uv tool run ruff check .          # same thing

# Install a tool globally (isolated), e.g. a CLI you use everywhere
uv tool install ruff

# Run a script with a temporary extra dependency
uv run --with rich python -c "import rich; print(rich.__version__)"
```

| Need | Command |
|------|---------|
| Part of the project (imported by your code) | `uv add pkg` |
| Dev tool for this project (pytest, ruff, mypy) | `uv add --dev pkg` |
| Tool you use everywhere (a CLI) | `uv tool install pkg` |
| One-off try-it-out | `uvx pkg` / `uv run --with pkg ...` |

---

## 9. Git, CI & README integration

**What to commit:** `pyproject.toml`, `uv.lock`, `.python-version`, `README.md`, `.gitignore`.
**What to ignore:** `.venv/`, `.env`, `__pycache__/`.

```gitignore
.venv/
.env
__pycache__/
```

**CI example (GitHub Actions)**, which runs checks on every PR and ties into protected branches from [Lesson 1](../../01-git-and-collaboration/README.md):

```yaml
# .github/workflows/ci.yml
name: CI
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --locked
      - run: uv run ruff check .
      - run: uv run mypy .
      - run: uv run pytest
```

> The action versions above (`checkout@v4`, `setup-uv@v5`) may be outdated by the time you read this. Check each action's page for the current major version. This workflow was not executed here.

**README "Installation" section for a uv project:**

````markdown
## Installation
```bash
git clone https://github.com/<user>/<repo>.git
cd <repo>
uv sync
cp .env.example .env     # then fill in your values
```

## Run / Test
```bash
uv run python -m my_app
uv run pytest
```
````

That's the entire setup a new contributor needs.

---

## 10. pip ↔ uv cheat sheet

| Task | pip / venv | uv (project) |
|------|-----------|--------------|
| Create env | `python -m venv .venv` | automatic (`uv sync` / `uv run`) |
| Activate | `source .venv/bin/activate` | not needed: `uv run ...` |
| Install a package | `pip install httpx` | `uv add httpx` |
| Install from requirements | `pip install -r requirements.txt` | `uv add -r requirements.txt` |
| Remove a package | `pip uninstall httpx` | `uv remove httpx` |
| Freeze versions | `pip freeze > requirements.txt` | automatic `uv.lock` (or `uv export`) |
| Recreate env | `pip install -r requirements.txt` | `uv sync` |
| Run a tool once | `pipx run ruff` | `uvx ruff` |
| Install a Python version | `pyenv install 3.12` | `uv python install 3.12` |

---

## 11. Common problems

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError` after `git pull` | Someone added a dependency | `uv sync` (or just `uv run ...`) |
| Works locally, fails in CI | Lockfile out of date | Run `uv lock`, commit `uv.lock`; use `uv sync --locked` in CI |
| Packages installed to the wrong place | Used `pip install` directly | Use `uv add` / `uv pip install` inside the project |
| Editor can't find packages | Editor is using a different interpreter | Point it at `.venv/bin/python` (VS Code: *Python: Select Interpreter*) |
| `No solution found when resolving dependencies` | Conflicting version requirements | Loosen a constraint; read which two packages conflict in the error |
| Merge conflict in `uv.lock` | Two branches changed dependencies | Merge `pyproject.toml` first, then run `uv lock` to regenerate (don't hand-edit) |
| `requires-python` error | Your Python is too old/new | `uv python install 3.12`, or adjust `requires-python` |
| `.venv` broken or stale | Python upgraded, folder moved | Delete `.venv`, run `uv sync` |
| Secrets in Git | `.env` not ignored | Add to `.gitignore`; rotate the keys |

> The `uv.lock` merge-conflict advice applies the idea from the [Lesson 1 conflict section](../../01-git-and-collaboration/README.md): never hand-resolve generated files, but regenerate them.

---

## 12. Exercise

1. Install uv and run `uv --version`.
2. Create a project: `uv init uv-practice && cd uv-practice`.
3. Run `uv run main.py` and look at what appeared (`.venv/`, `uv.lock`). Confirm `.venv/` does not show up in `git status`.
4. Add `httpx` and `pydantic` with `uv add`, and `pytest`, `ruff`, `mypy` with `uv add --dev`. Open `pyproject.toml` and find each one.
5. Run `uv tree` and identify a **transitive** dependency (one you didn't add directly).
6. Delete `.venv/` completely, then recreate it with `uv sync`. Confirm `uv run python -c "import httpx"` works.
7. Break the lock on purpose: edit a version range in `pyproject.toml` by hand, then run `uv sync --locked`. Read the error, then fix it with `uv lock`.
8. Copy settings from [`pyproject.example.toml`](./pyproject.example.toml) for `ruff`, `mypy`, and `pytest`, then run `uv run ruff check .`.
9. Upgrade only one package with `uv lock --upgrade-package httpx` and compare `git diff uv.lock`.
10. Add the README "Installation" section, push on a branch, and ask someone to clone and run it with only `uv sync`.

Stretch: add the CI workflow and mark it as a required check on `main`.

---

## 13. Self-check

- [ ] I can explain why each project gets its own virtual environment
- [ ] I know the difference between `pyproject.toml` (wants) and `uv.lock` (exact versions)
- [ ] I commit both `pyproject.toml` and `uv.lock`, and never commit `.venv/` or `.env`
- [ ] I use `uv add`, `uv remove`, `uv sync`, and `uv run` without thinking
- [ ] I know `--dev` dependencies are for tooling, and runtime dependencies are for the app
- [ ] I can reproduce any teammate's environment with `uv sync`
- [ ] I know `--locked` (CI) vs. `--frozen` and when to use each
- [ ] I can upgrade one package deliberately and review the lockfile diff
- [ ] I can pick between `uv add`, `uv tool install`, and `uvx`
- [ ] A stranger can clone my repo and run it from the README alone
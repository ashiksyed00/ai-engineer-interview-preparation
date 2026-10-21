# Phase 0 · Lesson 1: Git & Collaboration

> **Outcome:** Hand another developer your repo and they can understand, run, and contribute to it without you beside them.

## Contents

1. [Mental model](#1-mental-model-repos-commits-branches-remotes)
2. [Branch → PR → Merge workflow](#2-branch--pr--merge-workflow)
3. [Commit messages & history](#3-commit-messages--history)
4. [Resolving merge conflicts](#4-resolving-merge-conflicts)
5. [.gitignore & keeping secrets out](#5-gitignore--keeping-secrets-out)
6. [Writing a README](#6-writing-a-readme)
7. [Code review & protected branches](#7-code-review--protected-branches)
8. [Hands-on exercise](#8-hands-on-exercise)
9. [Self-check](#9-self-check)

---

## 1. Mental model: repos, commits, branches, remotes

| Term | Meaning |
|------|---------|
| **Repository (repo)** | A project folder + its full history (stored in `.git/`) |
| **Commit** | A snapshot of your project with a message, author, and a unique hash |
| **Branch** | A movable pointer to a commit. Lets you work in isolation |
| **Remote** | A copy of the repo hosted elsewhere (e.g. GitHub). Default name: `origin` |
| **Diff** | The line-by-line difference between two states |
| **Staging area (index)** | A "waiting room" where you choose which changes go into the next commit |

### The three areas + remote

```
Working Directory ──git add──▶ Staging Area ──git commit──▶ Local Repo ──git push──▶ Remote (GitHub)
        ◀────────────────────────── git pull / git fetch ◀──────────────────────────
```

### Essential commands

```bash
# one-time setup
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
git config --global init.defaultBranch main

# start a repo
git init                          # new local repo
git clone <url>                   # copy a remote repo

# daily loop
git status                        # what changed?
git diff                          # unstaged changes
git diff --staged                 # staged changes (what the commit will contain)
git add file.py                   # stage one file
git add -p                        # stage piece by piece (great habit)
git commit -m "message"           # save snapshot

# remotes
git remote -v                     # list remotes
git remote add origin <url>       # connect local repo to GitHub
git push -u origin main           # first push (sets upstream)
git fetch                         # download changes, don't merge
git pull                          # fetch + merge
```

---

## 2. Branch → PR → Merge workflow

**Rule: never commit directly to `main`.** Work on a branch.

```bash
# 1. Start from an up-to-date main
git switch main
git pull

# 2. Create a branch
git switch -c feat/add-chat-endpoint

# 3. Make changes, then commit small and often
git add -p
git commit -m "feat: add /chat endpoint"

# 4. Push the branch
git push -u origin feat/add-chat-endpoint

# 5. Open a Pull Request (GitHub UI, or CLI)
gh pr create --fill

# 6. Review → address feedback → push more commits (PR updates automatically)

# 7. Merge on GitHub (Squash / Merge / Rebase), then clean up
git switch main
git pull
git branch -d feat/add-chat-endpoint
```

**Branch naming:** `feat/…`, `fix/…`, `docs/…`, `chore/…`, `refactor/…`

**Merge options on GitHub:**

| Option | Result |
|--------|--------|
| Merge commit | Keeps all commits + adds a merge commit |
| Squash and merge | Combines the PR into one clean commit (popular default) |
| Rebase and merge | Replays commits linearly, no merge commit |

**Keep your branch up to date with main:**

```bash
git fetch origin
git merge origin/main        # simple, safe
# or: git rebase origin/main # cleaner history (don't rebase shared branches)
```

---

## 3. Commit messages & history

### Writing good messages

Use [Conventional Commits](https://www.conventionalcommits.org/): `type: short summary`

```
feat: add retry logic to LLM client
fix: handle empty prompt in /chat
docs: add setup steps to README
test: cover token counter edge cases
refactor: split data loader into module
chore: bump pydantic to 2.x
```

Rules of thumb:
- Imperative mood: "add", not "added"
- Summary ≤ ~50 chars; add a body (after a blank line) to explain **why**
- One logical change per commit
- Bad: `update`, `fix stuff`, `wip`, `final_final2`

### Inspecting history

```bash
git log --oneline                    # compact history
git log --oneline --graph --all      # branches visualized
git log -p file.py                   # history of one file with diffs
git log --author="Name" --since="2 weeks ago"
git show <hash>                      # one commit in detail
git blame file.py                    # who changed each line, and when
git diff main..feat/x                # compare branches
```

### Undoing things (know the safe vs. dangerous ones)

```bash
git restore file.py                  # discard unstaged changes in a file
git restore --staged file.py         # unstage (keep changes)
git commit --amend                   # fix the last commit (only if NOT pushed)
git revert <hash>                    # SAFE undo: creates a new "opposite" commit
git reset --hard <hash>              # DANGEROUS: destroys uncommitted work
git stash / git stash pop            # park changes temporarily
git reflog                           # safety net: find "lost" commits
```

> Never rewrite history (`reset --hard`, `--amend`, force push) on branches others use.

---

## 4. Resolving merge conflicts

A conflict happens when two branches change the **same lines**. Git stops and asks you to decide.

```bash
git merge origin/main
# CONFLICT (content): Merge conflict in app.py
```

Git marks the file like this:

```python
MODEL_NAME = "claude-sonnet"     # incoming version (the branch being merged in)
```

### Steps

1. `git status` → see files marked **both modified**
2. Open the file, decide what the final code should be (keep one, the other, or combine)
3. **Delete** the `<<<<<<<`, `=======`, `>>>>>>>` lines
4. Run the code/tests to verify
5. Finish:

```bash
git add app.py
git commit                # (or: git merge --continue)
```

Bail out anytime: `git merge --abort`

**Tips:** VS Code shows "Accept Current / Incoming / Both" buttons. Pull often and keep PRs small, since big, long-lived branches cause the worst conflicts.

---

## 5. .gitignore & keeping secrets out

`.gitignore` lists files Git should **never track**. Create it **before** your first commit.

### Python starter `.gitignore`

```gitignore
# Secrets & local config
.env
.env.*
!.env.example
*.pem
*.key
secrets.json

# Virtual environments
.venv/
venv/
env/

# Python generated files
__pycache__/
*.py[cod]
*.egg-info/
build/
dist/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# Notebooks
.ipynb_checkpoints/

# Data / models / outputs (too big or private)
data/raw/
*.ckpt
*.safetensors
outputs/

# OS / editor
.DS_Store
.vscode/
.idea/
```

### The secrets pattern: `.env` + `.env.example`

```bash
# .env  (real values, NEVER committed)
OPENAI_API_KEY=sk-real-key-here

# .env.example  (committed, shows what's needed)
OPENAI_API_KEY=your-key-here
```

```python
# load in Python:  pip install python-dotenv
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ["OPENAI_API_KEY"]
```

### Useful commands

```bash
git check-ignore -v .env            # why is this ignored?
git rm --cached file.py             # stop tracking a file already committed (keeps it on disk)
```

> **`.gitignore` does not affect files already tracked.** Use `git rm --cached` first.

### If you accidentally commit a secret

1. **Revoke / rotate the key immediately.** This is the real fix.
2. Remove it from the code and commit.
3. Optionally scrub history (`git filter-repo` or BFG), but assume it's already compromised.

Prevention: pre-commit hooks such as [`gitleaks`](https://github.com/gitleaks/gitleaks) or `detect-secrets`; GitHub also has push protection for known key formats.

---

## 6. Writing a README

A README answers: **What is it? How do I install, configure, run, test, and call it?**

````markdown
# Project Name

One-sentence description of what this does and why it exists.

## Features
- Feature one
- Feature two

## Requirements
- Python 3.11+

## Installation
```bash
git clone https://github.com/<user>/<repo>.git
cd <repo>
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration
Copy the example env file and fill in your values:
```bash
cp .env.example .env
```
| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | API key for the LLM provider | Yes |
| `LOG_LEVEL` | `INFO` or `DEBUG` | No |

## Usage
```bash
uvicorn app.main:app --reload
```
Server runs at http://localhost:8000 (docs at `/docs`).

## API Example
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```
Response:
```json
{"reply": "Hi! How can I help?"}
```

## Running Tests
```bash
pytest
```

## Project Structure
```
app/        # application code
tests/      # pytest tests
```

## Contributing
1. Branch from `main` (`feat/your-feature`)
2. Commit with clear messages
3. Open a PR; tests must pass

## License
MIT
````

**README test:** have someone follow it on a clean machine. Every place they get stuck is a bug in the README.

---

## 7. Code review & protected branches

### Pull Request best practices
- **Small PRs** (ideally < 400 lines changed), one purpose each
- Clear title + description: *what*, *why*, *how to test*, screenshots if useful
- Link issues: `Closes #12`
- Self-review your diff before requesting review

### Reviewing code
- Check: correctness, readability, tests, security (no secrets), edge cases
- Be specific and kind: suggest, don't demand ("Could we extract this into a helper?")
- Distinguish **blocking** issues from **nitpicks**

### Protected branches (GitHub → Settings → Branches → Add rule for `main`)

| Setting | Why |
|---------|-----|
| Require a pull request before merging | No direct pushes to `main` |
| Require ≥ 1 approval | Someone else looks at every change |
| Require status checks (CI/tests) to pass | Broken code can't merge |
| Require branch up to date before merging | Avoids merging stale code |
| Block force pushes & deletions | Protects history |

### Bonus: `CODEOWNERS` and a PR template

```
# .github/CODEOWNERS
*.py   @your-username
```

```markdown
<!-- .github/pull_request_template.md -->
## What & Why

## How to test

## Checklist
- [ ] Tests added/updated
- [ ] No secrets committed
- [ ] README/docs updated
```

---

## 8. Hands-on exercise

Build a tiny Python project and run the full workflow.

```bash
# 1. Create project
mkdir git-practice && cd git-practice
git init
python -m venv .venv

# 2. .gitignore FIRST, then verify venv is ignored
curl -o .gitignore https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore
git status                        # .venv should not appear

# 3. Add code + env example
echo 'print("hello")' > main.py
echo 'API_KEY=your-key-here' > .env.example
echo 'API_KEY=real-secret' > .env   # confirm: git status must NOT list .env

# 4. First commit + push (create an empty repo on GitHub first)
git add .
git commit -m "chore: initial commit"
git branch -M main
git remote add origin https://github.com/<you>/git-practice.git
git push -u origin main

# 5. Feature branch + PR
git switch -c feat/greeting
echo 'print("hello, AI engineer")' > main.py
git commit -am "feat: update greeting"
git push -u origin feat/greeting
gh pr create --fill               # or use the GitHub UI

# 6. Create a conflict on purpose
#    - On main: edit line 1 of main.py, commit
#    - On feat/greeting: edit the same line differently, commit
git merge main                    # conflict! resolve it, then git add + git commit

# 7. Explore history
git log --oneline --graph --all
```

**Stretch goals:** write a README using the template, turn on branch protection, and ask a friend to clone and run it from the README alone.

---

## 9. Self-check

- [ ] I can explain working dir vs. staging area vs. local repo vs. remote
- [ ] I never commit straight to `main`
- [ ] I can go branch → commit → push → PR → merge from memory
- [ ] My commit messages say *what* and *why*
- [ ] I can read conflict markers and resolve a conflict without panic
- [ ] `.env`, `.venv/`, and `__pycache__/` are ignored in all my projects
- [ ] I know what to do if a secret is pushed (rotate first!)
- [ ] My README lets a stranger install, configure, run, test, and call the project
- [ ] I know why protected branches and code review exist


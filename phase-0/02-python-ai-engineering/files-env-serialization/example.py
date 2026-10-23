"""Runnable examples: files, paths, env vars, JSON, JSONL, CSV, serialization.

Everything happens inside a temporary folder, so nothing is left behind.

Run:  python examples.py
"""

from __future__ import annotations

import csv
import json
import os
import tempfile
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Record:
    id: int
    text: str
    score: float
    created: datetime


# ---------------------------------------------------------------- 1. paths
def paths_demo(root: Path) -> None:
    data_dir = root / "data" / "raw"                 # build paths with /
    data_dir.mkdir(parents=True, exist_ok=True)      # no error if it exists
    f = data_dir / "notes.txt"

    print("name:", f.name, "| stem:", f.stem, "| suffix:", f.suffix)
    print("parent:", f.parent.name, "| exists:", f.exists())
    print("relative:", f.relative_to(root))

    f.write_text("line one\nline two\nline three\n", encoding="utf-8")
    print("read_text:", repr(f.read_text(encoding="utf-8")))

    # Iterate lines lazily (works for huge files)
    with f.open(encoding="utf-8") as fh:
        print("lines:", [line.strip() for line in fh])

    # Append mode
    with f.open("a", encoding="utf-8") as fh:
        fh.write("line four\n")

    # Find files
    (data_dir / "a.csv").touch()
    (data_dir / "b.csv").touch()
    print("csv files:", sorted(p.name for p in root.rglob("*.csv")))


# -------------------------------------------------------------- 2. env vars
def env_demo() -> None:
    os.environ["DEMO_TIMEOUT"] = "30"                # normally set in shell / .env

    api_key = os.environ.get("DEMO_API_KEY")         # None if missing
    timeout = int(os.environ.get("DEMO_TIMEOUT", "10"))   # env vars are ALWAYS strings
    debug = os.environ.get("DEMO_DEBUG", "false").lower() in {"1", "true", "yes"}
    print("api_key:", api_key, "| timeout:", timeout, "| debug:", debug)

    try:
        os.environ["DEMO_REQUIRED_SECRET"]           # fail fast on required settings
    except KeyError as exc:
        print("Missing required env var:", exc)


# ------------------------------------------------------------------ 3. JSON
def json_demo(root: Path) -> None:
    payload = {"name": "Ada", "tags": ["ml", "py"], "score": 0.9, "nested": {"ok": True}}
    path = root / "payload.json"

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    print("round trip equal:", loaded == payload)

    print(json.dumps({"city": "Zürich"}), json.dumps({"city": "Zürich"}, ensure_ascii=False))

    # Not everything is JSON-serializable
    rec = Record(1, "hello", 0.5, datetime(2026, 1, 2, 3, 4, 5))
    try:
        json.dumps(asdict(rec))
    except TypeError as exc:
        print("TypeError:", exc)

    print(json.dumps(asdict(rec), default=str))      # fallback converter

    # Invalid JSON -> JSONDecodeError (subclass of ValueError)
    try:
        json.loads("{'single': 'quotes'}")
    except json.JSONDecodeError as exc:
        print("JSONDecodeError:", exc.msg)


# --------------------------------------------------------- 4. JSONL (AI data)
def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")         # one JSON object per line


def read_jsonl(path: Path) -> Iterator[dict]:
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)               # lazy: one record at a time


def jsonl_demo(root: Path) -> None:
    path = root / "dataset.jsonl"
    write_jsonl(path, [{"prompt": "hi", "label": 1}, {"prompt": "bye", "label": 0}])
    print("jsonl:", list(read_jsonl(path)))


# ------------------------------------------------------------------- 5. CSV
def csv_demo(root: Path) -> None:
    path = root / "people.csv"
    rows = [{"name": "Ada", "age": 36}, {"name": "Bob", "age": 25}]

    with path.open("w", newline="", encoding="utf-8") as fh:    # newline="" is required
        writer = csv.DictWriter(fh, fieldnames=["name", "age"])
        writer.writeheader()
        writer.writerows(rows)

    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            print(row, "| age is str:", isinstance(row["age"], str))   # CSV has no types!


# ------------------------------------------------------ 6. safe (atomic) write
def atomic_write(path: Path, text: str) -> None:
    """Write to a temp file then replace, so readers never see a half-written file."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for demo, needs_root in (
            (paths_demo, True), (env_demo, False), (json_demo, True),
            (jsonl_demo, True), (csv_demo, True),
        ):
            print(f"\n--- {demo.__name__} ---")
            demo(root) if needs_root else demo()      # type: ignore[call-arg]

        target = root / "config.json"
        atomic_write(target, json.dumps({"v": 1}))
        print("\natomic write:", target.read_text())


if __name__ == "__main__":
    main()
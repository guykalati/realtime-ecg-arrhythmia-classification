"""Small local code/document search baseline for the new repair agent."""

import argparse
import json
import os
import re
import sqlite3
from contextlib import closing
from pathlib import Path


SUFFIXES = {".py", ".md", ".toml", ".txt"}
SKIP_DIRS = {".git", ".venv", "venv", "data", "results", "traces", "__pycache__"}
MAX_BYTES = 200_000
CHUNK_LINES = 50


def source_files(root: Path):
    root = root.resolve()
    for parent, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(files):
            path = Path(parent) / name
            if name.startswith(".") or path.suffix not in SUFFIXES or path.is_symlink():
                continue
            if path.stat().st_size > MAX_BYTES:
                continue
            yield path


def build_index(root: Path, database: Path) -> int:
    root = root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    database.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database)) as db, db:
        db.execute("DROP TABLE IF EXISTS chunks")
        db.execute("CREATE VIRTUAL TABLE chunks USING fts5(path UNINDEXED, line UNINDEXED, body)")
        count = 0
        for path in source_files(root):
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            for offset in range(0, len(lines), CHUNK_LINES):
                body = "\n".join(lines[offset : offset + CHUNK_LINES])
                if body.strip():
                    db.execute("INSERT INTO chunks(path, line, body) VALUES (?, ?, ?)",
                               (str(path.relative_to(root)), offset + 1, body))
                    count += 1
        db.commit()
    return count


def search(database: Path, terms: str, limit: int = 5) -> list[dict]:
    words = re.findall(r"[A-Za-z0-9_]+", terms)
    if not words:
        return []
    with closing(sqlite3.connect(database)) as db, db:
        statement = "SELECT path, line, body FROM chunks WHERE chunks MATCH ? ORDER BY bm25(chunks) LIMIT ?"
        rows = db.execute(statement, (" AND ".join(f'"{word}"' for word in words), limit)).fetchall()
        if not rows:
            rows = db.execute(statement, (" OR ".join(f'"{word}"' for word in words), limit)).fetchall()
    hits = []
    for path, start, body in rows:
        lines = body.splitlines()
        matched = next((i for i, line in enumerate(lines)
                        if any(word.lower() in line.lower() for word in words)), 0)
        lo, hi = max(0, matched - 2), min(len(lines), matched + 3)
        hits.append({"path": path, "line": int(start) + lo, "text": "\n".join(lines[lo:hi])})
    return hits


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    index = sub.add_parser("index")
    index.add_argument("root", type=Path)
    index.add_argument("database", type=Path)
    find = sub.add_parser("search")
    find.add_argument("database", type=Path)
    find.add_argument("terms")
    args = parser.parse_args()
    if args.action == "index":
        print(json.dumps({"chunks": build_index(args.root, args.database)}))
    else:
        print(json.dumps(search(args.database, args.terms), indent=2))


if __name__ == "__main__":
    main()

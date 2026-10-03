"""Search only explicitly supplied development experiment directories or ledger files."""

import argparse
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path


def build_index(experiments: list[Path], database: Path) -> int:
    if not experiments:
        raise ValueError("supply approved development experiment directories")
    database.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database)) as db, db:
        db.execute("DROP TABLE IF EXISTS runs")
        db.execute("CREATE VIRTUAL TABLE runs USING fts5(source UNINDEXED, run UNINDEXED, "
                   "status UNINDEXED, metric UNINDEXED, train_sha256 UNINDEXED, body)")
        count = 0
        for root in experiments:
            path = root if root.is_file() else root / "results.jsonl"
            if path.suffix != '.jsonl' or path.is_symlink() or not path.is_file():
                raise ValueError(f"missing or linked development ledger: {path}")
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                body = "\n".join(str(row.get(key, "")) for key in
                                 ("hypothesis", "failure_reason", "notes"))
                db.execute("INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?)",
                           (str(path.resolve()), int(row["run"]), row["status"],
                            row.get("metric_value"), row["train_sha256"], body))
                count += 1
        db.commit()
    return count


def search(database: Path, terms: str, limit: int = 5) -> list[dict]:
    words = re.findall(r"[A-Za-z0-9_]+", terms)
    if not words:
        return []
    expression = " OR ".join(f'"{word}"' for word in words)
    with closing(sqlite3.connect(database)) as db, db:
        rows = db.execute("SELECT source, run, status, metric, train_sha256, body "
                          "FROM runs WHERE runs MATCH ? ORDER BY bm25(runs) LIMIT ?",
                          (expression, limit)).fetchall()
    return [dict(zip(("source", "run", "status", "metric_value", "train_sha256", "text"), row))
            for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    index = sub.add_parser("index")
    index.add_argument("database", type=Path)
    index.add_argument("experiments", nargs="+", type=Path)
    find = sub.add_parser("search")
    find.add_argument("database", type=Path)
    find.add_argument("terms")
    args = parser.parse_args()
    if args.action == "index":
        print(json.dumps({"runs": build_index(args.experiments, args.database)}))
    else:
        print(json.dumps(search(args.database, args.terms), indent=2))


if __name__ == "__main__":
    main()

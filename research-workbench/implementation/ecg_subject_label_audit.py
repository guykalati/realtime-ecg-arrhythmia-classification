"""Audit primary MIT-BIH annotation symbols and matched experiment targets by subject."""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


CLASSES = ("N", "S", "V", "F")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(annotations: Path, targets: Path) -> dict:
    raw = defaultdict(Counter)
    matched = defaultdict(Counter)
    split_by_subject = {}
    records = defaultdict(set)
    with annotations.open(newline="") as source:
        for row in csv.DictReader(source):
            if row["primary_eligible"] != "1":
                continue
            subject = row["subject_group"]
            raw[subject][(row["class_5"], row["symbol"])] += 1
            records[subject].add(row["record_id"])
    with targets.open(newline="") as source:
        for row in csv.DictReader(source):
            subject = row["subject_group"]
            if row["class_4"] not in CLASSES or subject not in raw:
                raise ValueError("target class or subject absent from eligible annotations")
            previous = split_by_subject.setdefault(subject, row["split"])
            if previous != row["split"]:
                raise ValueError(f"subject crosses splits: {subject}")
            matched[subject][row["class_4"]] += 1
    rows = []
    for subject in sorted(raw, key=lambda value: (value != "201-202", value)):
        rows.append({"subject_group": subject, "records": sorted(records[subject]),
                     "split": split_by_subject.get(subject),
                     "raw_annotation_counts": {kind: sum(count for (cls, _), count in raw[subject].items()
                                                        if cls == kind) for kind in CLASSES},
                     "raw_symbols": {f"{cls}:{symbol}": count
                                     for (cls, symbol), count in sorted(raw[subject].items())},
                     "matched_target_counts": {kind: matched[subject][kind] for kind in CLASSES}})
    return {"source_sha256": {"annotations": digest(annotations), "targets": digest(targets)},
            "primary_subjects": len(rows), "subjects": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("annotations", type=Path)
    parser.add_argument("targets", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build(args.annotations, args.targets)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"subjects": result["primary_subjects"],
                      "F_by_subject": {row["subject_group"]: row["matched_target_counts"]["F"]
                                       for row in result["subjects"]
                                       if row["matched_target_counts"]["F"]}}, indent=2))


if __name__ == "__main__":
    main()

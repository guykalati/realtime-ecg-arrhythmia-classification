"""Propose subject-disjoint MIT-BIH splits from annotation counts, before fitting models."""

import argparse
import csv
import json
import random
from collections import Counter
from pathlib import Path

from ecg_split_guard import validate
from mitdb_beat_manifest import PACED_RECORDS, subject_group


SEED = 20260928
TRIALS = 50_000
PACED_ASSIGNMENT = {"102": "train", "107": "train", "104": "validation", "217": "test"}


def grouped_counts(record_counts: dict) -> tuple[dict, dict]:
    groups = {}
    members = {}
    for record_id, record in record_counts.items():
        if record_id in PACED_RECORDS:
            continue
        counts = record["class_counts"]
        group = subject_group(record_id)
        groups.setdefault(group, Counter()).update({klass: counts.get(klass, 0)
                                                     for klass in "NSVF"})
        members.setdefault(group, []).append(record_id)
    if len(groups) != 43 or sorted(members["201-202"]) != ["201", "202"]:
        raise ValueError("unexpected subject grouping")
    return groups, members


def totals(groups: dict, names: set[str]) -> Counter:
    result = Counter()
    for name in names:
        result.update(groups[name])
    return result


def choose(groups: dict) -> tuple[dict[str, set[str]], float]:
    remaining = sorted(set(groups) - {"208", "213"})
    rng = random.Random(SEED)
    overall = totals(groups, set(groups))
    targets = {"train": 30 / 43, "validation": 6 / 43, "test": 7 / 43}
    best, best_score = None, float("inf")
    for _ in range(TRIALS):
        rng.shuffle(remaining)
        split = {
            "validation": set(remaining[:6]),
            "test": {"208", *remaining[6:12]},
            "train": {"213", *remaining[12:]},
        }
        counts = {name: totals(groups, names) for name, names in split.items()}
        if counts["validation"]["F"] < 5:
            continue
        if any(counts[part][klass] == 0 for part in split for klass in "NSVF"):
            continue
        score = sum((counts[part][klass] / overall[klass] - targets[part]) ** 2
                    for part in split for klass in "NSV")
        if score < best_score:
            best, best_score = split, score
    if best is None:
        raise ValueError("no split met the predeclared class-support constraints")
    return best, best_score


def write_split(path: Path, assignment: dict[str, str], record_ids: set[str]) -> dict:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["record_id", "patient_id", "split"])
        for record_id in sorted(record_ids):
            writer.writerow([record_id, subject_group(record_id),
                             assignment[subject_group(record_id)]])
    return validate(path)


def propose(summary_path: Path, inventory_path: Path, output_dir: Path) -> dict:
    source = json.loads(summary_path.read_text())
    groups, members = grouped_counts(source["record_summary"])
    split, score = choose(groups)
    primary_a = {group: part for part, names in split.items() for group in names}
    primary_b = dict(primary_a)
    primary_b["208"], primary_b["213"] = primary_b["213"], primary_b["208"]
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {"seed": SEED, "candidate_permutations": TRIALS,
              "selection_uses": "annotated group class counts only; no signal values or model scores",
              "constraints": "43 groups: 30 train, 6 validation, 7 test; 213 train/208 test in A; "
                             "at least 5 validation F beats; each class present in each split",
              "objective": "squared N/S/V class-fraction deviation from group-count targets",
              "score_a": score, "folds": {}}
    for fold, primary in (("a", primary_a), ("b", primary_b)):
        assignment = dict(primary)
        assignment.update(PACED_ASSIGNMENT)
        csv_path = output_dir / f"candidate_split_{fold}.csv"
        check = write_split(csv_path, assignment, set(source["record_summary"]))
        validate(csv_path, inventory_path)
        class_counts = {}
        for part in ("train", "validation", "test"):
            group_names = {group for group, assigned in primary.items() if assigned == part}
            class_counts[part] = dict(sorted(totals(groups, group_names).items()))
        report["folds"][fold] = {
            "csv": str(csv_path), "validation": check,
            "primary_class_counts": class_counts,
            "primary_subject_groups": {part: sorted(names) for part, names in
                                       ((part, {g for g, a in primary.items() if a == part})
                                        for part in ("train", "validation", "test"))},
        }
    (output_dir / "candidate_split_summary.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("window_summary", type=Path)
    parser.add_argument("record_inventory", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    result = propose(args.window_summary, args.record_inventory, args.output_dir)
    print(json.dumps({"score_a": result["score_a"],
                      "fold_a_counts": result["folds"]["a"]["primary_class_counts"],
                      "fold_b_counts": result["folds"]["b"]["primary_class_counts"]}, indent=2))


if __name__ == "__main__":
    main()

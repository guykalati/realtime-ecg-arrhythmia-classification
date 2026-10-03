"""Freeze past-two-beat context indices and RR intervals for the approved comparison."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from mitdb_beat_manifest import PACED_RECORDS


CLASSES = "NSVF"


def build(window_manifest: Path, split_file: Path, output: Path, summary_file: Path) -> dict:
    with split_file.open(newline="", encoding="utf-8") as handle:
        split = {row["record_id"]: row for row in csv.DictReader(handle)}
    by_record = defaultdict(list)
    with window_manifest.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            by_record[row["record_id"]].append(row)
    if len(by_record) != 48 or len(split) != 48:
        raise ValueError("expected all 48 source records and split rows")
    output.parent.mkdir(parents=True, exist_ok=True)
    counts = defaultdict(Counter)
    excluded = Counter()
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["record_id", "subject_group", "split", "class_4", "target_index",
                         "prev1_index", "prev2_index", "rr1_seconds", "rr2_seconds"])
        for record_id in sorted(by_record):
            if record_id in PACED_RECORDS:
                continue
            rows = by_record[record_id]
            if [int(row["window_index"]) for row in rows] != list(range(len(rows))):
                raise ValueError(f"noncontiguous window indices in {record_id}")
            for i, row in enumerate(rows):
                if row["primary_eligible"] != "1" or row["class_5"] not in CLASSES:
                    continue
                if row["subject_group"] != split[record_id]["patient_id"]:
                    raise ValueError(f"subject mismatch in {record_id}")
                if i < 2:
                    excluded["first_two_windows"] += 1
                    continue
                prev1, prev2 = rows[i - 1], rows[i - 2]
                rr1 = (int(row["sample_index"]) - int(prev1["sample_index"])) / 360
                rr2 = (int(prev1["sample_index"]) - int(prev2["sample_index"])) / 360
                if rr1 <= 0 or rr2 <= 0:
                    excluded["nonpositive_rr"] += 1
                    continue
                part = split[record_id]["split"]
                if part not in ("train", "validation", "test"):
                    raise ValueError(f"bad split in {record_id}")
                writer.writerow([record_id, row["subject_group"], part, row["class_5"],
                                 row["window_index"], prev1["window_index"],
                                 prev2["window_index"], f"{rr1:.9f}", f"{rr2:.9f}"])
                counts[part][row["class_5"]] += 1
    summary = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
               "rule": "target plus two immediately preceding saved beat windows in same record; positive RR; no future context",
               "exclusions": dict(excluded),
               "class_counts": {part: dict(sorted(counts[part].items()))
                                for part in ("train", "validation", "test")},
               "total_targets": sum(sum(v.values()) for v in counts.values())}
    summary_file.write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("window_manifest", type=Path)
    parser.add_argument("split_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("summary_json", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.window_manifest, args.split_csv, args.output_csv,
                           args.summary_json), indent=2))


if __name__ == "__main__":
    main()

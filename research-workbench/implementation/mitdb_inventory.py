"""Read MIT-BIH record headers and annotations without assigning a split."""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import wfdb


def inspect(root: Path) -> dict:
    records = []
    for header_path in sorted(root.glob("[0-9][0-9][0-9].hea")):
        record_id = header_path.stem
        base = str(root / record_id)
        header = wfdb.rdheader(base)
        annotations = wfdb.rdann(base, "atr")
        counts = Counter(annotations.symbol)
        records.append({
            "record_id": record_id,
            "subject_group": "201-202" if record_id in {"201", "202"} else record_id,
            "sampling_hz": header.fs,
            "samples": header.sig_len,
            "leads": header.sig_name,
            "annotations": len(annotations.sample),
            "symbols": dict(sorted(counts.items())),
        })
    if len(records) != 48:
        raise ValueError(f"expected 48 MIT-BIH records, found {len(records)}")
    if len({r["subject_group"] for r in records}) != 47:
        raise ValueError("subject grouping must have 47 groups")
    if any(r["sampling_hz"] != 360 for r in records):
        raise ValueError("unexpected sampling rate")
    return {
        "source": "PhysioNet MIT-BIH Arrhythmia Database 1.0.0",
        "inspected_at_utc": datetime.now(timezone.utc).isoformat(),
        "records": records,
        "total_annotations": sum(r["annotations"] for r in records),
        "subject_groups": 47,
        "note": "All annotation symbols counted; beat-class mapping and train/test split are not assigned.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_directory", type=Path)
    parser.add_argument("output_json", type=Path)
    args = parser.parse_args()
    result = inspect(args.raw_directory)
    args.output_json.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"records": len(result["records"]),
                      "subject_groups": result["subject_groups"],
                      "total_annotations": result["total_annotations"]}))


if __name__ == "__main__":
    main()

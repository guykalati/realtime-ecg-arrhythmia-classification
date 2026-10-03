"""Reject record/patient overlap before any ECG preprocessing or training."""

import argparse
import csv
import json
from pathlib import Path


SPLITS = ("train", "validation", "test")


def validate(path: Path, inventory_path: Path | None = None) -> dict:
    records: dict[str, tuple[str, str]] = {}
    patients: dict[str, str] = {}
    counts = {part: 0 for part in SPLITS}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not {"record_id", "patient_id", "split"}.issubset(reader.fieldnames or []):
            raise ValueError("CSV needs record_id, patient_id, split columns")
        for row in reader:
            record = row["record_id"].strip()
            patient = row["patient_id"].strip()
            split = row["split"].strip()
            if not record or not patient or split not in SPLITS:
                raise ValueError(f"invalid row: {row}")
            if record in records:
                raise ValueError(f"duplicate record: {record}")
            if patient in patients and patients[patient] != split:
                raise ValueError(f"patient {patient} crosses {patients[patient]} and {split}")
            records[record] = patient, split
            patients[patient] = split
            counts[split] += 1
    if not records:
        raise ValueError("split file is empty")
    if "201" in records and "202" in records and records["201"][0] != records["202"][0]:
        raise ValueError("MIT-BIH records 201 and 202 come from the same subject")
    if inventory_path is not None:
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        expected = {row["record_id"] for row in inventory["records"]}
        if set(records) != expected:
            missing = sorted(expected - set(records))
            extra = sorted(set(records) - expected)
            raise ValueError(f"split does not cover inventory: missing={missing}, extra={extra}")
        groups: dict[str, str] = {}
        for row in inventory["records"]:
            group = row["subject_group"]
            patient = records[row["record_id"]][0]
            if group in groups and groups[group] != patient:
                raise ValueError(f"inventory subject group {group} has multiple patient IDs")
            groups[group] = patient
    return {"records": len(records), "patients": len(patients), "records_by_split": counts}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("split_csv", type=Path)
    parser.add_argument("--inventory", type=Path,
                        help="require exact coverage of a record inventory")
    args = parser.parse_args()
    print(json.dumps(validate(args.split_csv, args.inventory), indent=2))


if __name__ == "__main__":
    main()

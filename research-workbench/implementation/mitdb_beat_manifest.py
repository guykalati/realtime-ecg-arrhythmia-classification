"""Record every annotated MIT-BIH beat with source subject and AAMI-style class."""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

CLASS_SYMBOLS = {
    "N": "NLRej",
    "S": "AaJS",
    "V": "VE",
    "F": "F",
    "Q": "Q/f",
}
SYMBOL_CLASS = {symbol: klass for klass, symbols in CLASS_SYMBOLS.items()
                for symbol in symbols}
PACED_RECORDS = {"102", "104", "107", "217"}


def subject_group(record_id: str) -> str:
    return "201-202" if record_id in {"201", "202"} else record_id


def build(raw_dir: Path, csv_path: Path, summary_path: Path) -> dict:
    import wfdb

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    all_counts = Counter()
    primary_counts = Counter()
    record_counts = {}
    record_count = 0
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["record_id", "subject_group", "sample_index", "symbol",
                         "class_5", "primary_eligible", "lead_name"])
        for header_path in sorted(raw_dir.glob("[0-9][0-9][0-9].hea")):
            record_id = header_path.stem
            base = str(raw_dir / record_id)
            header = wfdb.rdheader(base)
            annotation = wfdb.rdann(base, "atr")
            if header.fs != 360:
                raise ValueError(f"unexpected sampling rate in {record_id}")
            if len(header.sig_name) != 2:
                raise ValueError(f"unexpected lead count in {record_id}")
            lead = "MLII" if "MLII" in header.sig_name else "V5"
            if lead not in header.sig_name:
                raise ValueError(f"no agreed lead in {record_id}: {header.sig_name}")
            local = Counter()
            seen_samples = set()
            for sample, symbol in zip(annotation.sample, annotation.symbol, strict=True):
                klass = SYMBOL_CLASS.get(symbol)
                if klass is None:
                    continue
                sample = int(sample)
                if not 0 <= sample < header.sig_len or sample in seen_samples:
                    raise ValueError(f"invalid or duplicate beat position {record_id}:{sample}")
                seen_samples.add(sample)
                primary = record_id not in PACED_RECORDS and klass != "Q"
                writer.writerow([record_id, subject_group(record_id), sample,
                                 symbol, klass, int(primary), lead])
                all_counts[klass] += 1
                local[klass] += 1
                if primary:
                    primary_counts[klass] += 1
            record_counts[record_id] = dict(local)
            record_count += 1
    if record_count != 48 or set(all_counts) != set(CLASS_SYMBOLS):
        raise ValueError("unexpected MIT-BIH record or class coverage")
    summary = {
        "source": "PhysioNet MIT-BIH Arrhythmia Database 1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "record_count": record_count,
        "subject_groups": len({subject_group(r) for r in record_counts}),
        "five_class_annotated_beats": dict(sorted(all_counts.items())),
        "primary_four_class_annotated_beats": dict(sorted(primary_counts.items())),
        "paced_records_excluded_from_primary": sorted(PACED_RECORDS),
        "record_class_counts": record_counts,
        "note": "Annotation positions and provisional classes only; waveform windows and split not generated.",
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_dir", type=Path)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("summary_path", type=Path)
    args = parser.parse_args()
    result = build(args.raw_dir, args.csv_path, args.summary_path)
    print(json.dumps({"records": result["record_count"],
                      "five_class": result["five_class_annotated_beats"],
                      "primary": result["primary_four_class_annotated_beats"]}, indent=2))


if __name__ == "__main__":
    main()

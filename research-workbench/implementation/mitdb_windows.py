"""Extract one-second raw-mV windows centered on annotated MIT-BIH beat locations."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


WIDTH = 360  # 0.5 s before and 0.5 s after at the source 360 Hz; no resampling.


def bounds(center: int) -> tuple[int, int]:
    return center - WIDTH // 2, center + WIDTH // 2


def extract(raw_dir: Path, beat_csv: Path, output_dir: Path,
            window_csv: Path, summary_path: Path) -> dict:
    import numpy as np
    import wfdb

    beats = defaultdict(list)
    with beat_csv.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            beats[row["record_id"]].append(row)
    if len(beats) != 48:
        raise ValueError(f"expected 48 records in beat manifest, found {len(beats)}")
    output_dir.mkdir(parents=True, exist_ok=True)
    window_csv.parent.mkdir(parents=True, exist_ok=True)
    kept, removed = Counter(), Counter()
    per_record = {}
    with window_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["record_id", "subject_group", "sample_index", "symbol",
                         "class_5", "primary_eligible", "lead_name", "window_index"])
        for record_id in sorted(beats):
            header = wfdb.rdheader(str(raw_dir / record_id))
            lead = beats[record_id][0]["lead_name"]
            channel = header.sig_name.index(lead)
            signal = wfdb.rdrecord(str(raw_dir / record_id), channels=[channel]).p_signal[:, 0]
            if len(signal) != header.sig_len or header.fs != 360:
                raise ValueError(f"signal/header mismatch in {record_id}")
            windows = []
            local = Counter()
            for row in beats[record_id]:
                center = int(row["sample_index"])
                start, end = bounds(center)
                if start < 0 or end > len(signal):
                    removed["edge"] += 1
                    continue
                window = signal[start:end]
                if len(window) != WIDTH or not np.isfinite(window).all():
                    removed["nonfinite_or_short"] += 1
                    continue
                writer.writerow([row["record_id"], row["subject_group"], center,
                                 row["symbol"], row["class_5"], row["primary_eligible"],
                                 lead, len(windows)])
                windows.append(window.astype(np.float32))
                kept[row["class_5"]] += 1
                if int(row["primary_eligible"]):
                    kept["primary_" + row["class_5"]] += 1
                local[row["class_5"]] += 1
            array = np.stack(windows) if windows else np.empty((0, WIDTH), dtype=np.float32)
            np.save(output_dir / f"{record_id}.npy", array)
            per_record[record_id] = {"lead_name": lead, "windows": len(array),
                                     "class_counts": dict(sorted(local.items()))}
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "PhysioNet MIT-BIH Arrhythmia Database 1.0.0",
        "window_samples": WIDTH,
        "sampling_hz": 360,
        "time_rule": "[R-peak - 180 samples, R-peak + 180 samples), no padding",
        "signal_units": "mV from WFDB p_signal, saved float32 without scaling",
        "lead_rule": "MLII by name; V5 only when MLII absent (records 102 and 104)",
        "kept_class_counts": dict(sorted(kept.items())),
        "removed_counts": dict(sorted(removed.items())),
        "record_summary": per_record,
        "note": "Reference R-peaks supplied by MIT-BIH; this is beat classification, not beat detection or a live model.",
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_dir", type=Path)
    parser.add_argument("beat_csv", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("window_csv", type=Path)
    parser.add_argument("summary_path", type=Path)
    args = parser.parse_args()
    result = extract(args.raw_dir, args.beat_csv, args.output_dir,
                     args.window_csv, args.summary_path)
    print(json.dumps({"kept": result["kept_class_counts"],
                      "removed": result["removed_counts"]}, indent=2))


if __name__ == "__main__":
    main()

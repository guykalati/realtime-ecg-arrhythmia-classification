"""Extract frozen one-second lead-II INCART windows for external four-class testing."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


LABELS = {"N": "N", "R": "N", "j": "N", "A": "S", "S": "S",
          "V": "V", "F": "F"}
SOURCE_WIDTH = 257
OUTPUT_WIDTH = 360


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(raw_dir: Path, output_dir: Path) -> dict:
    import numpy as np
    import scipy
    from scipy.signal import resample_poly
    import wfdb

    metadata_path = raw_dir / "metadata_inventory.json"
    signals_path = raw_dir / "signal_source_manifest.json"
    metadata = json.loads(metadata_path.read_text())
    signals = json.loads(signals_path.read_text())
    if len(metadata["records"]) != 75 or len(signals["files"]) != 75:
        raise ValueError("incomplete external source inventory")
    signal_hashes = {Path(item["key"]).name: item["sha256"] for item in signals["files"]}
    output_dir.mkdir(parents=True, exist_ok=True)
    windows_dir = output_dir / "windows_360"
    windows_dir.mkdir(exist_ok=True)
    kept, excluded = Counter(), Counter()
    per_record = {}
    manifest_path = output_dir / "window_manifest.csv"
    with manifest_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["record_id", "patient_id", "sample_index", "symbol",
                         "class_4", "lead_name", "window_index", "source_dat_sha256"])
        for record_info in metadata["records"]:
            record = record_info["record_id"]
            if f"{record}.dat" not in signal_hashes:
                raise ValueError(f"missing source signal hash: {record}")
            header = wfdb.rdheader(str(raw_dir / record))
            if header.fs != 257 or header.sig_name.index("II") != record_info["lead_ii_index"]:
                raise ValueError(f"lead or sampling mismatch: {record}")
            signal = wfdb.rdrecord(str(raw_dir / record),
                                   channels=[record_info["lead_ii_index"]]).p_signal[:, 0]
            annotation = wfdb.rdann(str(raw_dir / record), "atr")
            if len(signal) != header.sig_len or len(annotation.symbol) != record_info["annotation_events"]:
                raise ValueError(f"signal or annotation length mismatch: {record}")
            source_windows = []
            retained_rows = []
            seen_samples = set()
            local = Counter()
            for sample, symbol in zip(annotation.sample, annotation.symbol, strict=True):
                klass = LABELS.get(symbol)
                if klass is None:
                    excluded[f"symbol:{symbol}"] += 1
                    continue
                center = int(sample)
                if center in seen_samples:
                    raise ValueError(f"duplicate eligible beat position: {record}:{center}")
                seen_samples.add(center)
                start, end = center - 128, center + 129
                if start < 0 or end > len(signal):
                    excluded["edge"] += 1
                    continue
                window = signal[start:end]
                if len(window) != SOURCE_WIDTH or not np.isfinite(window).all():
                    excluded["nonfinite_or_short"] += 1
                    continue
                source_windows.append(window)
                retained_rows.append((center, symbol, klass))
                kept[klass] += 1
                local[klass] += 1
            if source_windows:
                raw_windows = np.asarray(source_windows, dtype=np.float32)
                resampled = resample_poly(raw_windows, OUTPUT_WIDTH, SOURCE_WIDTH,
                                          axis=1).astype(np.float32)
            else:
                resampled = np.empty((0, OUTPUT_WIDTH), dtype=np.float32)
            if resampled.shape != (len(retained_rows), OUTPUT_WIDTH) or \
                    not np.isfinite(resampled).all():
                raise ValueError(f"resampled window shape or finiteness: {record}")
            np.save(windows_dir / f"{record}.npy", resampled)
            for index, (sample, symbol, klass) in enumerate(retained_rows):
                writer.writerow([record, record_info["patient_id"], sample, symbol,
                                 klass, "II", index, signal_hashes[f"{record}.dat"]])
            per_record[record] = {"patient_id": record_info["patient_id"],
                                  "windows": len(retained_rows),
                                  "class_counts": dict(sorted(local.items()))}
    summary = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
               "source": "PhysioNet INCART 1.0.0", "source_metadata_sha256": sha256(metadata_path),
               "source_signals_manifest_sha256": sha256(signals_path),
               "window_rule": "257 lead-II mV samples [center-128,center+129), resample_poly(360,257)",
               "window_samples": OUTPUT_WIDTH, "wfdb_version": wfdb.__version__,
               "scipy_version": scipy.__version__, "kept_classes": dict(sorted(kept.items())),
               "excluded": dict(sorted(excluded.items())), "per_record": per_record,
               "manifest_sha256": sha256(manifest_path)}
    (output_dir / "window_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    result = extract(args.raw_dir, args.output_dir)
    print(json.dumps({"kept": result["kept_classes"], "excluded": result["excluded"]}, indent=2))


if __name__ == "__main__":
    main()

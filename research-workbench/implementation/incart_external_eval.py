"""One frozen INCART evaluation of the saved MIT-BIH weighted single-beat CNN."""

import argparse
import csv
import hashlib
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

from ecg_baseline import CLASSES, metrics
from ecg_context_compare import CNN, calibration


CHECKPOINT_SHA256 = "adcfff59c366ef8d70ea0188b287f799b5823406c888bc77c1f42f03fbf4d318"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(args) -> dict:
    started = time.monotonic()
    if sha256(args.checkpoint) != CHECKPOINT_SHA256:
        raise ValueError("weighted checkpoint hash does not match the frozen source")
    source = json.loads(args.mitdb_result.read_text())
    window_summary = json.loads(args.window_summary.read_text())
    if sha256(args.manifest) != window_summary["manifest_sha256"]:
        raise ValueError("INCART window manifest changed")
    if source["arms"]["single_weighted"]["selected_epoch"] != 10:
        raise ValueError("unexpected selected weighted epoch")
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    if checkpoint["epoch"] != 10 or checkpoint["context_sha256"] != source["context_sha256"] or \
            checkpoint["split_sha256"] != source["split_sha256"]:
        raise ValueError("checkpoint and MIT-BIH run provenance disagree")
    mean, std = source["train_waveform_mean"], source["train_waveform_std"]
    if not np.isfinite([mean, std]).all() or std <= 0:
        raise ValueError("invalid training-only scaling")
    model = CNN(context=False)
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    rows = defaultdict(list)
    patient_for_record = {}
    with args.manifest.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["class_4"] not in CLASSES or row["lead_name"] != "II":
                raise ValueError("unexpected label or lead")
            record, patient = row["record_id"], row["patient_id"]
            if patient_for_record.setdefault(record, patient) != patient:
                raise ValueError("record crosses patients")
            rows[record].append(row)
    if len(rows) != 75 or len(set(patient_for_record.values())) != 32:
        raise ValueError("unexpected record or patient coverage")
    actual, probabilities, subjects = [], [], []
    prediction_rows = []
    with torch.no_grad():
        for record in sorted(rows):
            array = np.load(args.windows_dir / f"{record}.npy", mmap_mode="r")
            record_rows = rows[record]
            if array.shape != (len(record_rows), 360):
                raise ValueError(f"window shape mismatch: {record}")
            if [int(row["window_index"]) for row in record_rows] != list(range(len(record_rows))):
                raise ValueError(f"window index mismatch: {record}")
            for start in range(0, len(record_rows), 512):
                batch_rows = record_rows[start:start + 512]
                batch = np.asarray(array[start:start + 512], dtype=np.float32)
                if not np.isfinite(batch).all():
                    raise ValueError(f"nonfinite external waveform: {record}")
                x = torch.from_numpy(np.ascontiguousarray(((batch - mean) / std)[:, None, :])).to(device)
                rr = torch.zeros((len(batch), 2), dtype=torch.float32, device=device)
                probs = model(x, rr).softmax(1).cpu().numpy()
                for row, probability in zip(batch_rows, probs, strict=True):
                    actual.append(CLASSES.index(row["class_4"]))
                    probabilities.append(probability)
                    subjects.append(row["patient_id"])
                    prediction_rows.append([row["record_id"], row["patient_id"],
                                            row["sample_index"], row["symbol"], row["class_4"],
                                            CLASSES[int(probability.argmax())],
                                            *[float(value) for value in probability]])
    y = np.asarray(actual, dtype=np.int64)
    p = np.asarray(probabilities, dtype=np.float32)
    subject_array = np.asarray(subjects)
    predicted = p.argmax(axis=1)
    result = metrics(y, predicted)
    result.update(calibration(y, p))
    result["cross_entropy"] = float(-np.log(np.maximum(p[np.arange(len(y)), y], 1e-12)).mean())
    result["per_patient"] = {patient: metrics(y[subject_array == patient],
                                              predicted[subject_array == patient])
                             for patient in sorted(set(subjects), key=int)}
    result.update({"generated_at_utc": datetime.now(timezone.utc).isoformat(),
                   "status": "success", "source": "PhysioNet INCART 1.0.0 external transfer",
                   "checkpoint_sha256": CHECKPOINT_SHA256,
                   "mitdb_result_sha256": sha256(args.mitdb_result),
                   "incart_manifest_sha256": sha256(args.manifest),
                   "incart_window_summary_sha256": sha256(args.window_summary),
                   "device": str(device), "torch_version": torch.__version__,
                   "elapsed_seconds": time.monotonic() - started,
                   "warning": "Reference annotated beats, lead-II and sampling shift; no beat detection or clinical deployment."})
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "predictions.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["record_id", "patient_id", "sample_index", "symbol", "actual",
                         "predicted", "p_N", "p_S", "p_V", "p_F"])
        writer.writerows(prediction_rows)
    result["predictions_sha256"] = sha256(args.output_dir / "predictions.csv")
    (args.output_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("windows_dir", "manifest", "window_summary", "checkpoint",
                 "mitdb_result", "output_dir"):
        parser.add_argument(name, type=Path)
    result = evaluate(parser.parse_args())
    print(json.dumps({"count": result["count"], "macro_f1": result["macro_f1_present_classes"],
                      "per_class_recall": {name: row["recall"] for name, row in result["per_class"].items()}}, indent=2))


if __name__ == "__main__":
    main()

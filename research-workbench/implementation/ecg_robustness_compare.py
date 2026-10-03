"""Frozen two-arm MIT-BIH training and exploratory INCART transfer comparison."""

import argparse
import csv
import json
import random
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from ecg_baseline import CLASSES, SEED, metrics, sha256
from ecg_context_compare import CNN, calibration, evaluate, load_parts
from ecg_waveform_transform import apply, fit


def external(model, params, windows_dir, manifest, device):
    rows = defaultdict(list)
    patients = {}
    with manifest.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            record, patient = row["record_id"], row["patient_id"]
            if row["class_4"] not in CLASSES or row["lead_name"] != "II":
                raise ValueError("unexpected INCART label or lead")
            if patients.setdefault(record, patient) != patient:
                raise ValueError("INCART record crosses patients")
            rows[record].append(row)
    if len(rows) != 75 or len(set(patients.values())) != 32:
        raise ValueError("INCART record/patient coverage changed")
    actual, probabilities, subjects = [], [], []
    model.eval()
    with torch.no_grad():
        for record in sorted(rows):
            array = np.load(windows_dir / f"{record}.npy", mmap_mode="r")
            record_rows = rows[record]
            if array.shape != (len(record_rows), 360) or \
                    [int(row["window_index"]) for row in record_rows] != list(range(len(record_rows))):
                raise ValueError(f"INCART window mismatch: {record}")
            for start in range(0, len(record_rows), 512):
                batch_rows = record_rows[start:start + 512]
                x = apply(np.asarray(array[start:start + 512], dtype=np.float32), params)
                x = torch.from_numpy(np.ascontiguousarray(x[:, None, :])).to(device)
                rr = torch.zeros((len(x), 2), dtype=torch.float32, device=device)
                p = model(x, rr).softmax(1).cpu().numpy()
                actual.extend(CLASSES.index(row["class_4"]) for row in batch_rows)
                probabilities.extend(p)
                subjects.extend(row["patient_id"] for row in batch_rows)
    y = np.asarray(actual, dtype=np.int64)
    p = np.asarray(probabilities, dtype=np.float32)
    if len(y) != 175777 or dict(Counter(CLASSES[index] for index in y)) != \
            {"N": 153594, "S": 1958, "V": 20006, "F": 219}:
        raise ValueError("INCART frozen support changed")
    predicted = p.argmax(1)
    result = metrics(y, predicted)
    result.update(calibration(y, p))
    result["cross_entropy"] = float(-np.log(np.maximum(p[np.arange(len(y)), y], 1e-12)).mean())
    subject_array = np.asarray(subjects)
    result["per_patient"] = {subject: metrics(y[subject_array == subject],
                                               predicted[subject_array == subject])
                             for subject in sorted(set(subjects), key=int)}
    return result


def run(args):
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required; do not run training on login node")
    started = time.monotonic()
    parts = load_parts(args.windows_dir, args.context_csv, args.split_csv)
    train = parts["train"]
    counts = np.bincount(train["y"], minlength=4)
    if np.any(counts == 0):
        raise ValueError("training class missing")
    weights = np.sqrt(counts[0] / counts)
    device = torch.device("cuda")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for mode in ("centered", "robust"):
        arm_started = time.monotonic()
        random.seed(SEED)
        np.random.seed(SEED)
        torch.manual_seed(SEED)
        torch.cuda.manual_seed_all(SEED)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        torch.cuda.reset_peak_memory_stats()
        params = fit(train["x"][:, 0, :], mode)
        loaders = {}
        for name, part in parts.items():
            x = apply(part["x"][:, 0, :], params)[:, None, :]
            rr = np.zeros((len(x), 2), dtype=np.float32)
            dataset = TensorDataset(torch.from_numpy(np.ascontiguousarray(x)),
                                    torch.from_numpy(rr), torch.from_numpy(part["y"]))
            loaders[name] = DataLoader(dataset, batch_size=256, shuffle=name == "train",
                                       num_workers=0, pin_memory=True,
                                       generator=torch.Generator().manual_seed(SEED))
        model = CNN(context=False).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=.001, weight_decay=.0001)
        criterion = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=device))
        best_loss, best_epoch, best_state = float("inf"), None, None
        history = []
        for epoch in range(1, 13):
            if time.monotonic() - started > 8 * 60:
                raise TimeoutError("8-minute internal cap before completed comparison")
            model.train()
            for x, rr, y in loaders["train"]:
                optimizer.zero_grad(set_to_none=True)
                loss = criterion(model(x.to(device), rr.to(device)), y.to(device))
                loss.backward()
                optimizer.step()
            val_loss, val_f1 = evaluate(model, loaders["validation"], device)
            history.append({"epoch": epoch, "validation_unweighted_cross_entropy": val_loss,
                            "validation_macro_f1": val_f1})
            print(json.dumps({"arm": mode, **history[-1]}), flush=True)
            if val_loss < best_loss:
                best_loss, best_epoch = val_loss, epoch
                best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
                torch.save({"state_dict": best_state, "epoch": epoch, "transform": params,
                            "context_sha256": sha256(args.context_csv),
                            "split_sha256": sha256(args.split_csv)},
                           args.output_dir / f"{mode}_best.pt")
        model.load_state_dict(best_state)
        test_loss, actual, p = evaluate(model, loaders["test"], device, detail=True)
        predicted = p.argmax(1)
        test = metrics(actual, predicted)
        test.update(calibration(actual, p))
        test["cross_entropy"] = test_loss
        subjects = parts["test"]["subjects"]
        test["per_subject"] = {subject: metrics(actual[subjects == subject], predicted[subjects == subject])
                               for subject in sorted(set(subjects))}
        external_result = external(model, params, args.incart_windows_dir, args.incart_manifest, device)
        results[mode] = {"selected_epoch": best_epoch,
                         "selected_validation_unweighted_cross_entropy": best_loss,
                         "validation_history": history, "transform": params,
                         "mitdb_development": test, "incart_development": external_result,
                         "parameter_count": sum(p.numel() for p in model.parameters()),
                         "elapsed_seconds": time.monotonic() - arm_started,
                         "gpu_peak_bytes": torch.cuda.max_memory_allocated(),
                         "checkpoint_sha256": sha256(args.output_dir / f"{mode}_best.pt")}
        print(json.dumps({"arm_complete": mode, "mitdb_macro_f1": test["macro_f1_present_classes"],
                          "incart_macro_f1": external_result["macro_f1_present_classes"]}), flush=True)
        (args.output_dir / "partial_result.json").write_text(json.dumps(results, indent=2) + "\n")
    result = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "status": "success",
              "split": "MIT-BIH candidate A, inspected development test",
              "external": "INCART previously inspected development transfer",
              "seed": SEED, "epochs": 12, "batch_size": 256,
              "optimizer": "AdamW lr=.001 weight_decay=.0001; lowest unweighted validation CE",
              "weights_sqrt_N_over_class": dict(zip(CLASSES, map(float, weights))),
              "counts": {name: dict(Counter(CLASSES[y] for y in part["y"])) for name, part in parts.items()},
              "context_sha256": sha256(args.context_csv), "split_sha256": sha256(args.split_csv),
              "incart_manifest_sha256": sha256(args.incart_manifest),
              "gpu_name": torch.cuda.get_device_name(), "torch_version": torch.__version__,
              "numpy_version": np.__version__, "elapsed_seconds": time.monotonic() - started,
              "arms": results}
    (args.output_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("windows_dir", "context_csv", "split_csv", "incart_windows_dir",
                 "incart_manifest", "output_dir"):
        parser.add_argument(name, type=Path)
    run(parser.parse_args())

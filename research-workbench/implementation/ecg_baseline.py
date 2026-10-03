"""One capped, subject-disjoint MIT-BIH single-beat CNN baseline."""

import argparse
import csv
import hashlib
import json
import random
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


CLASSES = "NSVF"
EXPECTED = {"train": 69904, "validation": 13720, "test": 17043}
SEED = 20260928


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_data(windows_dir: Path, manifest: Path, split_csv: Path):
    with split_csv.open(newline="", encoding="utf-8") as handle:
        split_rows = list(csv.DictReader(handle))
    if len(split_rows) != 48 or len({row["record_id"] for row in split_rows}) != 48:
        raise ValueError("split must contain all 48 unique records")
    split = {row["record_id"]: row for row in split_rows}
    patient_part = {}
    for row in split_rows:
        old = patient_part.setdefault(row["patient_id"], row["split"])
        if old != row["split"]:
            raise ValueError("subject crosses partitions")
    by_record = defaultdict(list)
    with manifest.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["record_id"] not in split or row["subject_group"] != split[row["record_id"]]["patient_id"]:
                raise ValueError("window manifest and split disagree on subject")
            if row["primary_eligible"] == "1" and row["class_5"] in CLASSES:
                by_record[row["record_id"]].append(row)
    parts = {name: {"x": [], "y": [], "subjects": []} for name in EXPECTED}
    for record_id in sorted(by_record):
        rows = by_record[record_id]
        array = np.load(windows_dir / f"{record_id}.npy", mmap_mode="r")
        indices = np.array([int(row["window_index"]) for row in rows])
        if array.ndim != 2 or array.shape[1] != 360 or np.any(indices >= len(array)):
            raise ValueError(f"bad window shape or index: {record_id}")
        name = split[record_id]["split"]
        if name not in parts:
            raise ValueError(f"unknown split {name}")
        part = parts[name]
        part["x"].append(np.asarray(array[indices], dtype=np.float32))
        part["y"].extend(CLASSES.index(row["class_5"]) for row in rows)
        part["subjects"].extend(row["subject_group"] for row in rows)
    for name, part in parts.items():
        part["x"] = np.concatenate(part["x"])
        part["y"] = np.asarray(part["y"], dtype=np.int64)
        if len(part["x"]) != EXPECTED[name] or not np.isfinite(part["x"]).all():
            raise ValueError(f"unexpected count or nonfinite windows in {name}")
    return parts


class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        layers = []
        channels = 1
        for next_channels, kernel in ((16, 7), (32, 5), (64, 3)):
            layers.extend((nn.Conv1d(channels, next_channels, kernel, padding=kernel // 2),
                           nn.ReLU(), nn.MaxPool1d(2)))
            channels = next_channels
        layers.extend((nn.AdaptiveAvgPool1d(1), nn.Flatten(), nn.Linear(64, 4)))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


def evaluate(model, loader, device):
    model.eval()
    criterion = nn.CrossEntropyLoss(reduction="sum")
    actual, predicted, loss = [], [], 0.0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            logits = model(x)
            loss += criterion(logits, y).item()
            actual.extend(y.cpu().tolist())
            predicted.extend(logits.argmax(1).cpu().tolist())
    return loss / len(actual), np.asarray(actual), np.asarray(predicted)


def metrics(actual, predicted):
    matrix = np.bincount(4 * actual + predicted, minlength=16).reshape(4, 4)
    per_class = {}
    for i, klass in enumerate(CLASSES):
        tp = int(matrix[i, i])
        support = int(matrix[i].sum())
        predicted_count = int(matrix[:, i].sum())
        precision = tp / predicted_count if predicted_count else 0.0
        recall = tp / support if support else None
        f1 = 2 * precision * recall / (precision + recall) if recall is not None and precision + recall else (0.0 if support else None)
        per_class[klass] = {"support": support, "precision": precision if support else None,
                            "recall": recall, "f1": f1}
    f1s = [row["f1"] for row in per_class.values() if row["f1"] is not None]
    return {"count": int(matrix.sum()), "accuracy": float(matrix.trace() / matrix.sum()),
            "macro_f1_present_classes": float(sum(f1s) / len(f1s)),
            "confusion_matrix_rows_actual_columns_predicted": matrix.tolist(),
            "per_class": per_class}


def run(args):
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU unavailable; baseline must not run on the login node")
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    started = time.monotonic()
    parts = load_data(args.windows_dir, args.manifest, args.split)
    mean = float(parts["train"]["x"].mean(dtype=np.float64))
    std = float(parts["train"]["x"].std(dtype=np.float64))
    if not np.isfinite(std) or std <= 0:
        raise ValueError("invalid training standard deviation")
    loaders = {}
    for name, part in parts.items():
        part["x"] -= mean
        part["x"] /= std
        dataset = TensorDataset(torch.from_numpy(part["x"][:, None, :]), torch.from_numpy(part["y"]))
        loaders[name] = DataLoader(dataset, batch_size=256, shuffle=name == "train",
                                   num_workers=0, pin_memory=True,
                                   generator=torch.Generator().manual_seed(SEED))
    device = torch.device("cuda")
    model = CNN().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.0001)
    criterion = nn.CrossEntropyLoss()
    best_loss, best_epoch, best_state = float("inf"), None, None
    history = []
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for epoch in range(1, 13):
        if time.monotonic() - started > 25 * 60:
            raise TimeoutError("25-minute internal cap reached before 12 epochs; no held-out test run")
        model.train()
        for x, y in loaders["train"]:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(x), y)
            loss.backward()
            optimizer.step()
        val_loss, actual, predicted = evaluate(model, loaders["validation"], device)
        row = {"epoch": epoch, "validation_loss": val_loss,
               "validation_macro_f1": metrics(actual, predicted)["macro_f1_present_classes"],
               "elapsed_seconds": time.monotonic() - started}
        history.append(row)
        print(json.dumps(row), flush=True)
        if val_loss < best_loss:
            best_loss, best_epoch = val_loss, epoch
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
            torch.save({"state_dict": best_state, "epoch": epoch,
                        "split_sha256": sha256(args.split),
                        "manifest_sha256": sha256(args.manifest)},
                       args.output_dir / "best.pt")
    model.load_state_dict(best_state)
    test_loss, actual, predicted = evaluate(model, loaders["test"], device)
    test = metrics(actual, predicted)
    test["cross_entropy"] = test_loss
    subjects = np.asarray(parts["test"]["subjects"])
    test["per_subject"] = {subject: metrics(actual[subjects == subject], predicted[subjects == subject])
                           for subject in sorted(set(subjects))}
    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "success", "seed": SEED, "epochs": 12, "batch_size": 256,
        "architecture": "Conv1d 1-16-32-64, kernels 7-5-3, ReLU/maxpool2, global average pooling, linear 64-4",
        "optimizer": "AdamW lr=0.001 weight_decay=0.0001; unweighted cross entropy",
        "window_manifest_sha256": sha256(args.manifest), "split_sha256": sha256(args.split),
        "train_mean_mv": mean, "train_std_mv": std,
        "counts": {name: len(part["y"]) for name, part in parts.items()},
        "validation_history": history, "selected_epoch": best_epoch,
        "selected_validation_loss": best_loss, "test": test,
        "elapsed_seconds": time.monotonic() - started,
        "gpu_peak_bytes": torch.cuda.max_memory_allocated(),
        "gpu_name": torch.cuda.get_device_name(), "torch_version": torch.__version__,
        "numpy_version": np.__version__,
        "note": "Reference-peak beat classification; test evaluated once after selecting by validation loss.",
    }
    (args.output_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("windows_dir", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("split", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    result = run(args)
    print(json.dumps({"selected_epoch": result["selected_epoch"],
                      "test_macro_f1": result["test"]["macro_f1_present_classes"]}), flush=True)


if __name__ == "__main__":
    main()

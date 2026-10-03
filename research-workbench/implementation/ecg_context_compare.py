"""Matched three-arm, subject-disjoint MIT-BIH development comparison."""

import argparse
import csv
import json
import random
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from ecg_baseline import CLASSES, SEED, metrics, sha256

EXPECTED = {"train": 69842, "validation": 13708, "test": 17029}


class CNN(nn.Module):
    def __init__(self, context=False):
        super().__init__()
        channels = 3 if context else 1
        layers = []
        for next_channels, kernel in ((16, 7), (32, 5), (64, 3)):
            layers += [nn.Conv1d(channels, next_channels, kernel, padding=kernel // 2),
                       nn.ReLU(), nn.MaxPool1d(2)]
            channels = next_channels
        self.features = nn.Sequential(*layers, nn.AdaptiveAvgPool1d(1), nn.Flatten())
        self.head = nn.Linear(66 if context else 64, 4)
        self.context = context

    def forward(self, x, rr):
        features = self.features(x)
        if self.context:
            features = torch.cat((features, rr), dim=1)
        return self.head(features)


def load_parts(windows_dir, context_csv, split_csv, expected=None):
    expected = EXPECTED if expected is None else expected
    with split_csv.open(newline="", encoding="utf-8") as handle:
        split_rows = list(csv.DictReader(handle))
    split = {row["record_id"]: row for row in split_rows}
    if len(split_rows) != 48 or len(split) != 48:
        raise ValueError("split must have 48 unique records")
    patient_parts = {}
    for row in split_rows:
        previous = patient_parts.setdefault(row["patient_id"], row["split"])
        if previous != row["split"]:
            raise ValueError("subject crosses partitions")
    with context_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != sum(expected.values()):
        raise ValueError("context manifest target count changed")
    arrays = {}
    parts = {name: {"x": [], "rr": [], "y": [], "subjects": []} for name in expected}
    for row in rows:
        record = row["record_id"]
        if record not in split or row["subject_group"] != split[record]["patient_id"] or row["split"] != split[record]["split"]:
            raise ValueError("context and split disagree")
        indices = [int(row[key]) for key in ("target_index", "prev1_index", "prev2_index")]
        if not indices[0] > indices[1] > indices[2] >= 0:
            raise ValueError("nonpast context")
        if record not in arrays:
            arrays[record] = np.load(windows_dir / f"{record}.npy", mmap_mode="r")
            if arrays[record].ndim != 2 or arrays[record].shape[1] != 360:
                raise ValueError("bad waveform shape")
        if indices[0] >= len(arrays[record]):
            raise ValueError("window index out of bounds")
        rr = [float(row["rr1_seconds"]), float(row["rr2_seconds"])]
        if not all(np.isfinite(rr)) or min(rr) <= 0:
            raise ValueError("invalid RR")
        part = parts[row["split"]]
        part["x"].append(arrays[record][indices])
        part["rr"].append(rr)
        part["y"].append(CLASSES.index(row["class_4"]))
        part["subjects"].append(row["subject_group"])
    for name, part in parts.items():
        part["x"] = np.asarray(part["x"], dtype=np.float32)
        part["rr"] = np.asarray(part["rr"], dtype=np.float32)
        part["y"] = np.asarray(part["y"], dtype=np.int64)
        part["subjects"] = np.asarray(part["subjects"])
        if len(part["y"]) != expected[name] or not np.isfinite(part["x"]).all():
            raise ValueError(f"unexpected count or invalid waveform: {name}")
    return parts


def evaluate(model, loader, device, detail=False):
    model.eval()
    loss_sum = 0.0
    ys, probs = [], []
    with torch.no_grad():
        for x, rr, y in loader:
            logits = model(x.to(device), rr.to(device))
            loss_sum += nn.functional.cross_entropy(logits, y.to(device), reduction="sum").item()
            ys.append(y.numpy())
            probs.append(logits.softmax(1).cpu().numpy())
    actual = np.concatenate(ys)
    probabilities = np.concatenate(probs)
    if detail:
        return loss_sum / len(actual), actual, probabilities
    return loss_sum / len(actual), metrics(actual, probabilities.argmax(1))["macro_f1_present_classes"]


def calibration(actual, probabilities):
    confidence = probabilities.max(axis=1)
    correct = (probabilities.argmax(axis=1) == actual).astype(float)
    ece, bins = 0.0, []
    for i in range(10):
        mask = (confidence >= i / 10) & (confidence <= (i + 1) / 10 if i == 9 else confidence < (i + 1) / 10)
        if mask.any():
            mean_confidence = float(confidence[mask].mean())
            accuracy = float(correct[mask].mean())
            ece += mask.mean() * abs(accuracy - mean_confidence)
            bins.append({"bin": i, "count": int(mask.sum()), "accuracy": accuracy, "confidence": mean_confidence})
    onehot = np.eye(4)[actual]
    return {"brier_multiclass": float(np.mean(np.sum((probabilities - onehot) ** 2, axis=1))),
            "ece_10_equal_width": float(ece), "calibration_bins": bins}


def run(args):
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required; do not train on login node")
    started = time.monotonic()
    parts = load_parts(args.windows_dir, args.context_csv, args.split_csv)
    train = parts["train"]
    mean = float(train["x"][:, 0, :].mean(dtype=np.float64))
    std = float(train["x"][:, 0, :].std(dtype=np.float64))
    rr_mean = train["rr"].mean(axis=0, dtype=np.float64)
    rr_std = train["rr"].std(axis=0, dtype=np.float64)
    if std <= 0 or np.any(rr_std <= 0):
        raise ValueError("invalid train scaling")
    for part in parts.values():
        part["x"] = (part["x"] - mean) / std
        part["rr"] = ((part["rr"] - rr_mean) / rr_std).astype(np.float32)
    counts = np.bincount(train["y"], minlength=4)
    if np.any(counts == 0):
        raise ValueError("class missing from train")
    weights = np.sqrt(counts[0] / counts)
    device = torch.device("cuda")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for arm, context, weighted in (("single_unweighted", False, False),
                                   ("single_weighted", False, True),
                                   ("past2_rr_weighted", True, True)):
        arm_started = time.monotonic()
        random.seed(SEED)
        np.random.seed(SEED)
        torch.manual_seed(SEED)
        torch.cuda.manual_seed_all(SEED)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        torch.cuda.reset_peak_memory_stats()
        loaders = {}
        for name, part in parts.items():
            x = part["x"] if context else part["x"][:, :1, :]
            dataset = TensorDataset(torch.from_numpy(np.ascontiguousarray(x)),
                                    torch.from_numpy(np.ascontiguousarray(part["rr"])),
                                    torch.from_numpy(part["y"]))
            loaders[name] = DataLoader(dataset, batch_size=256, shuffle=name == "train",
                                       num_workers=0, pin_memory=True,
                                       generator=torch.Generator().manual_seed(SEED))
        model = CNN(context).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.0001)
        criterion = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=device) if weighted else None)
        best_loss, best_epoch, best_state = float("inf"), None, None
        history = []
        for epoch in range(1, 13):
            if time.monotonic() - started > 8 * 60:
                raise TimeoutError("8-minute internal cap before complete three-arm comparison")
            model.train()
            for x, rr, y in loaders["train"]:
                optimizer.zero_grad(set_to_none=True)
                loss = criterion(model(x.to(device), rr.to(device)), y.to(device))
                loss.backward()
                optimizer.step()
            val_loss, val_f1 = evaluate(model, loaders["validation"], device)
            history.append({"epoch": epoch, "validation_unweighted_cross_entropy": val_loss,
                            "validation_macro_f1": val_f1})
            print(json.dumps({"arm": arm, **history[-1]}), flush=True)
            if val_loss < best_loss:
                best_loss, best_epoch = val_loss, epoch
                best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
                torch.save({"state_dict": best_state, "epoch": epoch,
                            "context_sha256": sha256(args.context_csv), "split_sha256": sha256(args.split_csv)},
                           args.output_dir / f"{arm}_best.pt")
        model.load_state_dict(best_state)
        test_loss, actual, probabilities = evaluate(model, loaders["test"], device, detail=True)
        predicted = probabilities.argmax(1)
        test = metrics(actual, predicted)
        test.update(calibration(actual, probabilities))
        test["cross_entropy"] = test_loss
        subjects = parts["test"]["subjects"]
        test["per_subject"] = {subject: metrics(actual[subjects == subject], predicted[subjects == subject])
                               for subject in sorted(set(subjects))}
        results[arm] = {"selected_epoch": best_epoch, "selected_validation_unweighted_cross_entropy": best_loss,
                        "validation_history": history, "test_development": test,
                        "parameter_count": sum(p.numel() for p in model.parameters()),
                        "elapsed_seconds": time.monotonic() - arm_started,
                        "gpu_peak_bytes": torch.cuda.max_memory_allocated()}
        print(json.dumps({"arm_complete": arm, "selected_epoch": best_epoch,
                          "test_macro_f1": test["macro_f1_present_classes"]}), flush=True)
    result = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "status": "success", "split": "candidate A, inspected development test",
              "target_rule": "same targets in all arms; target plus two past saved beats only",
              "seed": SEED, "epochs": 12, "batch_size": 256,
              "optimizer": "AdamW lr=.001 weight_decay=.0001; checkpoint lowest unweighted validation CE",
              "weights_sqrt_N_over_class": dict(zip(CLASSES, map(float, weights))),
              "train_waveform_mean": mean, "train_waveform_std": std,
              "train_rr_mean": rr_mean.tolist(), "train_rr_std": rr_std.tolist(),
              "counts": {name: dict(Counter(CLASSES[y] for y in part["y"])) for name, part in parts.items()},
              "context_sha256": sha256(args.context_csv), "split_sha256": sha256(args.split_csv),
              "gpu_name": torch.cuda.get_device_name(), "torch_version": torch.__version__,
              "numpy_version": np.__version__, "elapsed_seconds": time.monotonic() - started,
              "arms": results}
    (args.output_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("windows_dir", "context_csv", "split_csv", "output_dir"):
        parser.add_argument(name, type=Path)
    run(parser.parse_args())

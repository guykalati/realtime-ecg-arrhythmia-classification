"""Frozen confidence versus training-feature novelty abstention comparison."""

import argparse
import csv
import json
import math
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

from ecg_baseline import CLASSES, metrics, sha256
from ecg_context_compare import CNN, calibration, load_parts
from ecg_waveform_transform import apply

EXPECTED = {
    "checkpoint": "d33678d4b77da35a03566e2c8e9cd43125b27f78ab2a2373af1df6f6eb989e15",
    "context": "94d5d9c7064f5c9e4c33921f8f140670f4a1e8605b807cd21259c9865562d089",
    "split": "192f31b83654a6779e1fd79bb97e6b47646709097695d9ca2a449652f9d0e6b3",
    "incart": "03074e47abfa84ce101ab93db1c1085cfd29407689e5393e602f57b3134d432a",
}
LAMBDAS = (0.0, 0.25, 0.5, 1.0)
SELECT_COVERAGES = (0.5, 0.6, 0.7, 0.8, 0.9)
REPORT_COVERAGES = (0.5, 0.7, 0.9)


def infer(model, loader, device):
    model.eval()
    ys, probabilities, features = [], [], []
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            z = model.features(x)
            p = model.head(z).softmax(1)
            ys.append(y.numpy())
            probabilities.append(p.cpu().numpy())
            features.append(z.cpu().numpy())
    return (np.concatenate(ys), np.concatenate(probabilities), np.concatenate(features))


def loader(x, y, transform):
    x = apply(x, transform)[:, None, :]
    return DataLoader(TensorDataset(torch.from_numpy(np.ascontiguousarray(x)),
                                    torch.from_numpy(np.asarray(y, dtype=np.int64))),
                      batch_size=512, shuffle=False, num_workers=0, pin_memory=True)


def infer_incart(model, args, transform, device):
    rows, patients = defaultdict(list), {}
    with args.incart_manifest.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            record, patient = row["record_id"], row["patient_id"]
            if row["class_4"] not in CLASSES or row["lead_name"] != "II":
                raise ValueError("unexpected INCART label or lead")
            if patients.setdefault(record, patient) != patient:
                raise ValueError("INCART patient mapping changed")
            rows[record].append(row)
    if len(rows) != 75 or len(set(patients.values())) != 32:
        raise ValueError("INCART record/patient coverage changed")
    all_y, all_p, all_z, groups = [], [], [], []
    for record in sorted(rows):
        record_rows = rows[record]
        x = np.load(args.incart_windows_dir / f"{record}.npy", mmap_mode="r")
        if x.shape != (len(record_rows), 360) or \
                [int(row["window_index"]) for row in record_rows] != list(range(len(record_rows))):
            raise ValueError(f"INCART window mismatch: {record}")
        y = np.asarray([CLASSES.index(row["class_4"]) for row in record_rows], dtype=np.int64)
        yy, p, z = infer(model, loader(np.asarray(x, dtype=np.float32), y, transform), device)
        all_y.append(yy)
        all_p.append(p)
        all_z.append(z)
        groups.extend([patients[record]] * len(y))
    y = np.concatenate(all_y)
    if len(y) != 175777 or dict(Counter(CLASSES[i] for i in y)) != \
            {"N": 153594, "S": 1958, "V": 20006, "F": 219}:
        raise ValueError("INCART frozen support changed")
    return y, np.concatenate(all_p), np.concatenate(all_z), np.asarray(groups)


def novelty(features, mean, scale, sorted_train_distance):
    distance = np.mean(((features - mean) / scale) ** 2, axis=1)
    percentile = np.searchsorted(sorted_train_distance, distance, side="right") / len(sorted_train_distance)
    return percentile.astype(np.float32)


def validation_curve(y, p, novelty_percentile, weight):
    score = 1 - p.max(1) + weight * novelty_percentile
    order = np.argsort(score, kind="stable")
    wrong = (p.argmax(1) != y).astype(np.float64)
    rows = []
    for coverage in SELECT_COVERAGES:
        n = math.ceil(coverage * len(y))
        rows.append({"target_coverage": coverage, "retained": n,
                     "selective_error": float(wrong[order[:n]].mean())})
    return score, rows, float(np.mean([row["selective_error"] for row in rows]))


def policy_summary(y, p, score, groups, cutoffs):
    prediction = p.argmax(1)
    wrong = prediction != y
    all_metrics = metrics(y, prediction)
    all_metrics.update(calibration(y, p))
    all_metrics["cross_entropy"] = float(-np.log(np.maximum(p[np.arange(len(y)), y], 1e-12)).mean())
    result = {"count": len(y), "all_beats": all_metrics, "cutoffs": {}}
    for target, cutoff in cutoffs.items():
        accepted = score <= cutoff
        n = int(accepted.sum())
        row = {"score_cutoff_from_validation": float(cutoff), "retained": n,
               "actual_coverage": n / len(y),
               "selective_error": float(wrong[accepted].mean()) if n else None,
               "per_true_class": {}, "per_group": {}}
        for index, cls in enumerate(CLASSES):
            mask = y == index
            row["per_true_class"][cls] = {"support": int(mask.sum()),
                                          "retained": int((mask & accepted).sum()),
                                          "retention": float(accepted[mask].mean()) if mask.any() else None}
        if n:
            row["accepted_metrics"] = metrics(y[accepted], prediction[accepted])
        for group in sorted(set(groups)):
            mask = groups == group
            kept = mask & accepted
            row["per_group"][str(group)] = {"support": int(mask.sum()),
                                             "retained": int(kept.sum()),
                                             "retention": float(accepted[mask].mean()),
                                             "selective_error": float(wrong[kept].mean()) if kept.any() else None}
        result["cutoffs"][str(target)] = row
    return result


def run(args):
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required; do not run inference on login node")
    observed = {"checkpoint": sha256(args.checkpoint), "context": sha256(args.context_csv),
                "split": sha256(args.split_csv), "incart": sha256(args.incart_manifest)}
    if observed != EXPECTED:
        raise ValueError(f"frozen input hash mismatch: {observed}")
    started = time.monotonic()
    device = torch.device("cuda")
    saved = torch.load(args.checkpoint, map_location=device, weights_only=False)
    transform = saved["transform"]
    if saved["epoch"] != 10 or transform["mode"] != "centered" or \
            not np.isclose(transform["global_std"], 0.34301185886458335, rtol=0, atol=1e-9):
        raise ValueError("unexpected centered reference checkpoint")
    model = CNN(context=False).to(device)
    model.load_state_dict(saved["state_dict"])
    parts = load_parts(args.windows_dir, args.context_csv, args.split_csv)
    inferred = {}
    for name, part in parts.items():
        inferred[name] = infer(model, loader(part["x"][:, 0, :], part["y"], transform), device)
        if time.monotonic() - started > 8 * 60:
            raise TimeoutError("8-minute inference cap")
    incart_y, incart_p, incart_z, incart_groups = infer_incart(model, args, transform, device)
    train_z = inferred["train"][2].astype(np.float64)
    mean = train_z.mean(axis=0)
    scale = np.maximum(train_z.std(axis=0), 1e-6)
    sorted_distance = np.sort(np.mean(((train_z - mean) / scale) ** 2, axis=1))
    arrays = {}
    for name, (y, p, z) in inferred.items():
        arrays[name] = (y, p, novelty(z, mean, scale, sorted_distance), parts[name]["subjects"])
    arrays["incart"] = (incart_y, incart_p,
                        novelty(incart_z, mean, scale, sorted_distance), incart_groups)
    for name, expected_macro in (("test", 0.6340281378596991), ("incart", 0.4020395975530835)):
        y, p, _, _ = arrays[name]
        score = metrics(y, p.argmax(1))["macro_f1_present_classes"]
        if not np.isclose(score, expected_macro, rtol=0, atol=1e-10):
            raise ValueError(f"reference prediction mismatch on {name}: {score}")

    val_y, val_p, val_novelty, _ = arrays["validation"]
    curves, scores, cutoffs = {}, {}, {}
    for weight in LAMBDAS:
        val_score, rows, mean_error = validation_curve(val_y, val_p, val_novelty, weight)
        key = str(weight)
        curves[key] = {"mean_selective_error": mean_error, "points": rows}
        scores[key] = val_score
        ordered = np.sort(val_score)
        cutoffs[key] = {str(c): float(ordered[math.ceil(c * len(val_y)) - 1])
                        for c in REPORT_COVERAGES}
    selected = min(LAMBDAS, key=lambda weight: (curves[str(weight)]["mean_selective_error"], weight))
    results = {}
    for weight in sorted({0.0, selected}):
        key = str(weight)
        results[key] = {}
        for name in ("validation", "test", "incart"):
            y, p, novelty_percentile, groups = arrays[name]
            score = 1 - p.max(1) + weight * novelty_percentile
            results[key][name] = policy_summary(y, p, score, groups, cutoffs[key])

    args.output_dir.mkdir(parents=True, exist_ok=True)
    score_file = args.output_dir / "scores.npz"
    np.savez_compressed(score_file, **{
        f"{name}_{field}": values
        for name, (y, p, novelty_percentile, groups) in arrays.items()
        for field, values in (("y", y.astype(np.int8)), ("p", p.astype(np.float32)),
                              ("novelty", novelty_percentile), ("group", groups))
    })
    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(), "status": "success",
        "model": "fixed centered CNN", "reference_checkpoint_sha256": observed["checkpoint"],
        "input_hashes": observed, "runner_sha256": sha256(Path(__file__)),
        "train_feature_mean": mean.tolist(), "train_feature_scale": scale.tolist(),
        "train_novelty_distance_min_median_max": [float(sorted_distance[0]),
                                                 float(np.median(sorted_distance)),
                                                 float(sorted_distance[-1])],
        "validation_curves": curves, "validation_cutoffs": cutoffs,
        "selected_lambda": selected, "policies": results,
        "scores_sha256": sha256(score_file), "elapsed_seconds": time.monotonic() - started,
        "gpu_name": torch.cuda.get_device_name(), "gpu_peak_bytes": torch.cuda.max_memory_allocated(),
        "torch_version": torch.__version__, "numpy_version": np.__version__,
    }
    (args.output_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"complete": True, "selected_lambda": selected,
                      "validation_mean_errors": {k: v["mean_selective_error"] for k, v in curves.items()},
                      "elapsed_seconds": result["elapsed_seconds"]}), flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("checkpoint", "windows_dir", "context_csv", "split_csv",
                 "incart_windows_dir", "incart_manifest", "output_dir"):
        parser.add_argument(name, type=Path)
    run(parser.parse_args())

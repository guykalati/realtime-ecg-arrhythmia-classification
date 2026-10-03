"""One frozen compact multi-scale ECG development arm; see protocol."""

import argparse
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
from ecg_context_compare import calibration, evaluate, load_parts
from ecg_robustness_compare import external
from ecg_waveform_transform import apply, fit

EXPECTED_INPUT_HASHES = {
    "context": "94d5d9c7064f5c9e4c33921f8f140670f4a1e8605b807cd21259c9865562d089",
    "split": "192f31b83654a6779e1fd79bb97e6b47646709097695d9ca2a449652f9d0e6b3",
    "incart": "03074e47abfa84ce101ab93db1c1085cfd29407689e5393e602f57b3134d432a",
}


class MultiScaleCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.branches = nn.ModuleList([
            nn.Sequential(nn.Conv1d(1, 16, kernel, padding=kernel // 2), nn.ReLU())
            for kernel in (3, 7, 15)
        ])
        self.features = nn.Sequential(
            nn.MaxPool1d(2),
            nn.Conv1d(48, 64, 5, padding=2), nn.ReLU(), nn.MaxPool1d(2),
            nn.Conv1d(64, 64, 3, padding=1), nn.ReLU(),
            nn.AdaptiveAvgPool1d(1), nn.Flatten(),
        )
        self.gate = nn.Sequential(nn.Linear(64, 8), nn.ReLU(), nn.Linear(8, 64), nn.Sigmoid())
        self.head = nn.Linear(64, 4)

    def forward(self, x, rr):
        features = self.features(torch.cat([branch(x) for branch in self.branches], dim=1))
        return self.head(features * self.gate(features))


def run(args):
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required; do not train on login node")
    observed = {"context": sha256(args.context_csv), "split": sha256(args.split_csv),
                "incart": sha256(args.incart_manifest)}
    if observed != EXPECTED_INPUT_HASHES:
        raise ValueError(f"frozen input manifest hash changed: {observed}")
    started = time.monotonic()
    parts = load_parts(args.windows_dir, args.context_csv, args.split_csv)
    counts = np.bincount(parts["train"]["y"], minlength=4)
    if np.any(counts == 0):
        raise ValueError("training class missing")
    weights = np.sqrt(counts[0] / counts)
    transform = fit(parts["train"]["x"][:, 0, :], "centered")
    if not np.isclose(transform["global_std"], 0.34301185886458335, rtol=0, atol=1e-9):
        raise ValueError("centered training scaler differs from reference")
    loaders = {}
    for name, part in parts.items():
        x = apply(part["x"][:, 0, :], transform)[:, None, :]
        rr = np.zeros((len(x), 2), dtype=np.float32)
        loaders[name] = DataLoader(
            TensorDataset(torch.from_numpy(np.ascontiguousarray(x)), torch.from_numpy(rr),
                          torch.from_numpy(part["y"])),
            batch_size=256, shuffle=name == "train", num_workers=0, pin_memory=True,
            generator=torch.Generator().manual_seed(SEED),
        )

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.cuda.reset_peak_memory_stats()
    device = torch.device("cuda")
    model = MultiScaleCNN().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.001, weight_decay=.0001)
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=device))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = args.output_dir / "multiscale_best.pt"
    best_loss, best_epoch, history = float("inf"), None, []
    for epoch in range(1, 13):
        if time.monotonic() - started > 8 * 60:
            raise TimeoutError("8-minute internal training cap")
        model.train()
        for x, rr, y in loaders["train"]:
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(x.to(device), rr.to(device)), y.to(device))
            loss.backward()
            optimizer.step()
        val_loss, val_f1 = evaluate(model, loaders["validation"], device)
        history.append({"epoch": epoch, "validation_unweighted_cross_entropy": val_loss,
                        "validation_macro_f1": val_f1})
        print(json.dumps(history[-1]), flush=True)
        if val_loss < best_loss:
            best_loss, best_epoch = val_loss, epoch
            torch.save({"state_dict": {key: value.detach().cpu().clone()
                                       for key, value in model.state_dict().items()},
                        "epoch": epoch, "transform": transform,
                        "context_sha256": sha256(args.context_csv),
                        "split_sha256": sha256(args.split_csv)}, checkpoint)
    saved = torch.load(checkpoint, map_location=device, weights_only=False)
    model.load_state_dict(saved["state_dict"])
    if saved["epoch"] != best_epoch or saved["transform"] != transform:
        raise ValueError("selected checkpoint does not match training selection")

    test_loss, actual, probabilities = evaluate(model, loaders["test"], device, detail=True)
    predicted = probabilities.argmax(1)
    test = metrics(actual, predicted)
    test.update(calibration(actual, probabilities))
    test["cross_entropy"] = test_loss
    subjects = parts["test"]["subjects"]
    test["per_subject"] = {subject: metrics(actual[subjects == subject], predicted[subjects == subject])
                           for subject in sorted(set(subjects))}
    incart = external(model, transform, args.incart_windows_dir, args.incart_manifest, device)
    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(), "status": "success",
        "scope": "inspected MIT-BIH candidate A and INCART development data",
        "model": "parallel kernels 3/7/15, 16 channels each, 64-channel stack, SE-8 head",
        "seed": SEED, "epochs": 12, "batch_size": 256,
        "optimizer": "AdamW lr=.001 weight_decay=.0001; lowest unweighted validation CE",
        "weights_sqrt_N_over_class": dict(zip(CLASSES, map(float, weights))),
        "counts": {name: dict(Counter(CLASSES[y] for y in part["y"])) for name, part in parts.items()},
        "transform": transform, "selected_epoch": best_epoch,
        "selected_validation_unweighted_cross_entropy": best_loss,
        "validation_history": history, "mitdb_development": test, "incart_development": incart,
        "parameter_count": sum(p.numel() for p in model.parameters()),
        "gpu_peak_bytes": torch.cuda.max_memory_allocated(),
        "elapsed_seconds": time.monotonic() - started,
        "gpu_name": torch.cuda.get_device_name(), "torch_version": torch.__version__,
        "numpy_version": np.__version__, "runner_sha256": sha256(Path(__file__)),
        "context_sha256": sha256(args.context_csv), "split_sha256": sha256(args.split_csv),
        "incart_manifest_sha256": sha256(args.incart_manifest),
        "checkpoint_sha256": sha256(checkpoint),
    }
    (args.output_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"complete": True, "mitdb_macro_f1": test["macro_f1_present_classes"],
                      "incart_macro_f1": incart["macro_f1_present_classes"]}), flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("windows_dir", "context_csv", "split_csv", "incart_windows_dir",
                 "incart_manifest", "output_dir"):
        parser.add_argument(name, type=Path)
    run(parser.parse_args())

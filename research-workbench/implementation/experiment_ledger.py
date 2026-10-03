"""Freeze and audit a bounded autoresearch-style experiment batch."""

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_file(root: Path, relative: Path) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("frozen files must stay inside the experiment directory")
    return path


def initialize(root: Path, prepare: Path, data_manifest: Path, metric: str,
               direction: str, max_runs: int, max_seconds: float) -> dict:
    if max_runs < 1 or not math.isfinite(max_seconds) or max_seconds <= 0 or direction not in {"min", "max"} or not metric.strip():
        raise ValueError("invalid run budget or direction")
    config_path = root / "experiment.json"
    if config_path.exists() or (root / "results.jsonl").exists():
        raise FileExistsError("experiment already initialized; use a fresh directory")
    config = {
        "metric": metric,
        "direction": direction,
        "max_runs": max_runs,
        "max_training_seconds_per_run": max_seconds,
        "prepare_file": str(prepare),
        "prepare_sha256": digest(local_file(root, prepare)),
        "data_manifest_file": str(data_manifest),
        "data_manifest_sha256": digest(local_file(root, data_manifest)),
    }
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    return config


def records(root: Path) -> list[dict]:
    path = root / "results.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def record(root: Path, result: dict) -> dict:
    config = json.loads((root / "experiment.json").read_text())
    for key in ("prepare", "data_manifest"):
        path = local_file(root, Path(config[f"{key}_file"]))
        if digest(path) != config[f"{key}_sha256"]:
            raise ValueError(f"frozen {key} changed: {path}")
    history = records(root)
    if len(history) >= config["max_runs"]:
        raise ValueError("approved run count exhausted")
    status = result.get("status")
    if status not in {"success", "failed"}:
        raise ValueError("status must be success or failed")
    seconds = float(result["training_seconds"])
    if not math.isfinite(seconds) or seconds < 0 or seconds > config["max_training_seconds_per_run"]:
        raise ValueError("training time exceeds approved per-run budget")
    value = result.get("metric_value")
    if status == "success" and (not isinstance(value, (int, float)) or not math.isfinite(value)):
        raise ValueError("successful run needs a finite metric_value")
    candidate_file = Path(result.get("candidate_file", "train.py"))
    if candidate_file.is_absolute() or ".." in candidate_file.parts or candidate_file.name != "train.py":
        raise ValueError("candidate must be a train.py inside the experiment directory")
    if (root / candidate_file).is_symlink():
        raise ValueError("candidate train.py missing or linked")
    candidate = local_file(root, candidate_file)
    if not candidate.is_file():
        raise ValueError("candidate train.py missing or linked")
    entry = {
        "run": len(history) + 1,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "metric_name": config["metric"],
        "metric_value": value if status == "success" else None,
        "training_seconds": seconds,
        "train_sha256": digest(candidate),
        "candidate_file": candidate_file.as_posix(),
        "hypothesis": str(result.get("hypothesis", "")),
        "failure_reason": str(result.get("failure_reason", "")),
        "notes": str(result.get("notes", "")),
    }
    with (root / "results.jsonl").open("a") as handle:
        handle.write(json.dumps(entry) + "\n")
    return entry


def summary(root: Path) -> dict:
    config = json.loads((root / "experiment.json").read_text())
    history = records(root)
    successful = [item for item in history if item["status"] == "success"]
    best = (min if config["direction"] == "min" else max)(
        successful, key=lambda item: item["metric_value"], default=None
    )
    return {"runs": len(history), "remaining": config["max_runs"] - len(history), "best": best}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    init = sub.add_parser("init")
    init.add_argument("root", type=Path)
    init.add_argument("--prepare", type=Path, required=True)
    init.add_argument("--data-manifest", type=Path, required=True)
    init.add_argument("--metric", required=True)
    init.add_argument("--direction", choices=["min", "max"], required=True)
    init.add_argument("--max-runs", type=int, required=True)
    init.add_argument("--max-seconds", type=float, required=True)
    add = sub.add_parser("record")
    add.add_argument("root", type=Path)
    add.add_argument("result_json", type=Path)
    show = sub.add_parser("summary")
    show.add_argument("root", type=Path)
    args = parser.parse_args()
    if args.action == "init":
        output = initialize(args.root, args.prepare, args.data_manifest, args.metric,
                            args.direction, args.max_runs, args.max_seconds)
    elif args.action == "record":
        output = record(args.root, json.loads(args.result_json.read_text()))
    else:
        output = summary(args.root)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

"""Training-only waveform transform parameters for the ECG robustness comparison."""

import numpy as np


def core(x: np.ndarray, mode: str, floor: float | None = None) -> np.ndarray:
    if x.ndim != 2 or x.shape[1] != 360 or not np.isfinite(x).all():
        raise ValueError("expected finite [beats, 360] waveforms")
    medians = np.median(x, axis=1, keepdims=True)
    centered = x - medians
    if mode == "centered":
        return centered
    if mode == "robust":
        if floor is None or not np.isfinite(floor) or floor <= 0:
            raise ValueError("positive training-derived robust floor required")
        scales = 1.4826 * np.median(np.abs(centered), axis=1, keepdims=True)
        return centered / np.maximum(scales, floor)
    raise ValueError("unknown waveform transform")


def fit(train: np.ndarray, mode: str) -> dict:
    if mode not in {"centered", "robust"}:
        raise ValueError("unknown waveform transform")
    if train.ndim != 2 or train.shape[1] != 360 or not len(train) or not np.isfinite(train).all():
        raise ValueError("expected nonempty finite [beats, 360] training waveforms")
    floor = None
    if mode == "robust":
        medians = np.median(train, axis=1, keepdims=True)
        scales = 1.4826 * np.median(np.abs(train - medians), axis=1)
        positive = scales[scales > 0]
        if not len(positive):
            raise ValueError("no positive training robust scales")
        floor = float(np.percentile(positive, 5))
    transformed = core(train, mode, floor)
    std = float(transformed.std(dtype=np.float64))
    if not np.isfinite(std) or std <= 0:
        raise ValueError("invalid training global standard deviation")
    return {"mode": mode, "floor": floor, "global_std": std}


def apply(x: np.ndarray, params: dict) -> np.ndarray:
    std = params["global_std"]
    if not np.isfinite(std) or std <= 0:
        raise ValueError("invalid saved global standard deviation")
    return (core(x, params["mode"], params.get("floor")) / std).astype(np.float32)

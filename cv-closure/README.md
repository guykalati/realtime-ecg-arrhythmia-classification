# Five-class ECG classification and replay

The CV functionality now has a real saved model and a working interface. The new patient-disjoint score differs from the historical beat-split result: **94.10% accuracy, macro F1 0.6722, weighted F1 0.9334 on 19,253 test beats**. This is a single-seed result. Fusion recall is **0/384** and must be disclosed alongside aggregate accuracy. Q includes paced and unclassified annotations. Total dataset: **109,438** beat windows, 48 records, 47 subject groups.

The selected checkpoint is epoch9 of24, chosen solely by validation cross entropy. Source, split, waveform and checkpoint hashes are in `output/result.json`; all held-out predictions are in `output/test_predictions.npz`. The 50-beat replay is balanced for demonstration and is not the test distribution. NumPy inference matches an independent PyTorch float32 CPU reference within 0.000004 logits. Original GPU export used reduced-precision convolution arithmetic; the CPU export audit preserves that difference.

## Run the demo

From this directory, install NumPy in an isolated environment, then:

```sh
python demo.py --verify
python verify_results.py
python demo.py --port 8793
```

Open http://127.0.0.1:8793. Start/pause/reset, recorded-beat selection, waveform rendering and model-driven simulated alerts were verified in the browser (`output/browser_audit.json`, screenshot). Every request runs the saved model; predictions are not a hard-coded replay. Inference median was about0.51ms on this Mac over50small windows; this excludes browser/server overhead and is not a clinical response-time claim.

## Reproduce data and training

Requires NumPy, WFDB4.3.1 and PyTorch2.5.1+CUDA12.4 (original cluster environment). Use an allocated GPU, not a login node.

```sh
mkdir -p data
python download_mitdb.py data/raw
python mitdb_beat_manifest.py data/raw data/beats.csv data/beats_summary.json
python mitdb_windows.py data/raw data/beats.csv data/windows data/window_manifest.csv data/windows_summary.json
python train.py data/windows data/window_manifest.csv split.csv new-output
```

MIT-BIH source: https://physionet.org/content/mitdb/1.0.0/ (Open Data Commons Attribution license). Acquisition manifest and per-waveform hashes preserve the exact snapshot. Raw data and PyTorch checkpoint stay outside Git; the portable NumPy weights needed by the demo are included. To verify a newly trained model export, point `verify_export.py` at its output directory and run within a CPU/GPU allocation; this script uses `output/` by default.

## Meaning and limits

Five-class reference-peak classification is implemented and evaluated. The interface replays recorded one-second windows and emits an alert when the predicted class is S/V/F/Q. This is simulated monitoring, with annotated locations, uncalibrated probabilities and no clinical validation. It does not implement continuous ECG acquisition or beat detection. These match the CV's prototype/simulated-alert scope; stronger deployment claims require later work.

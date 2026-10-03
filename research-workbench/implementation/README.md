# realtime-ecg-arrhythmia-classification: implementation snapshot

This directory contains this project's code, audit artifacts, manifests, and finite experiment ledgers through 3 October 2026. Shared foundation helpers are included because the original foundation tests exercise all three pipelines.

The reports one level up preserve the shared research history. Code for the other projects is in their own repository branches. Historical local/cluster paths and frozen manifests are preserved as evidence. They need explicit path configuration for a new machine; they are not portable one-command launchers.

Raw datasets, model weights, environments, model caches, and raw data-directory outputs are excluded. Reported checksums identify those external artifacts. No excluded data should be inferred to exist after cloning.

Run the lightweight checks from this directory:

```bash
python3 -m unittest -v test_foundations.py
```

Original cross-project workbench instructions are archived in `WORKBENCH_HISTORY.md`. See `../CURRENT_STATUS_2026-10-03.md` for the latest state.

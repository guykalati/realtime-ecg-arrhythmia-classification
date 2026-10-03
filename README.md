# Subject-aware ECG beat classification

This branch preserves the original course artifacts and adds the new personal research work through 3 October 2026.

- [Current status](research-workbench/CURRENT_STATUS_2026-10-03.md)
- [Plain-language HTML walkthrough](research-workbench/output/portfolio_progress_explained_2026-10-03.html) — download/open locally
- [Implementation and checks](research-workbench/implementation/README.md)
- [First audit](research-workbench/FIRST_SCAN_2026-09-27.md)
- [Original README](LEGACY_README.md) — historical claims, corrected by the audit

## Status

The18-cell timing ablation completed and passed its audit (job22001343,307GPU-seconds). The combined waveform/past-RR model passed the frozen provisional rule:mean INCART macroF1 rose0.396→0.498 and S F1 rose0.024→0.274 across six comparisons. Rare F remains weak (mean recall0.18% MIT/4.95% INCART), with substantial false alarms. Exact cross-source input screen covers771,896windows with zero matches; it does not establish patient independence. EDB remains unscored and SVDB reserved.

## Snapshot layout

`research-workbench/implementation` holds project code and compact evidence. Shared foundation helpers and cross-project reports preserve dependencies and the original audit trail. Large raw datasets, checkpoints, model caches, and virtual environments remain external.

Historical reports record earlier stopping points. Read the current status before interpreting older pending statements. The new work does not establish clinical deployment, autonomous-research superiority, or unpublished benchmark claims.

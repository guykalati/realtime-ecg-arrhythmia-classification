# ECG checkpoint selection — 30 September 2026

Six paired 100-epoch trajectories completed in Slurm array **21890695**: split A, CNN and multi-scale, three seeds. Each saved the earliest minimum validation CE and earliest maximum validation macro-F1 checkpoints. All six histories exactly match the earlier frozen trajectories; differences below therefore isolate checkpoint selection. All 12 checkpoint hashes, selection rules, counts, MIT per-beat and per-subject metrics passed [the audit](implementation/ecg_selection_audit_2026-09-30.json). INCART consistency is checked from saved confusion matrices, without a fresh inference run.

| Model / policy | Mean MIT development macro F1 | Mean INCART development macro F1 |
|---|---:|---:|
| CNN / CE | .57806 | .39455 |
| CNN / macro F1 | .53115 | .37716 |
| Multi-scale / CE | .59651 | .40339 |
| Multi-scale / macro F1 | .53762 | .41158 |

Paired macro-minus-CE mean ± sample SD: CNN MIT −.04691 ± .04954, INCART −.01738 ± .01802; multi-scale MIT −.05888 ± .05121, INCART +.00819 ± .00878. These are descriptive three-seed differences, not confidence intervals or confirmation.

Macro selection increases INCART S recall (CNN .2766→.4717; multi-scale .0713→.1970), but S precision remains only .0231/.0259. Multi-scale F recall rises .0533→.1431 while F precision falls .00346→.00262. This is a false-positive tradeoff, not reliable rare-class detection.

Calibration also worsens. Mean MIT ECE: CNN .02469→.03486, multi-scale .02264→.06519; mean INCART ECE: CNN .10381→.17119, multi-scale .07792→.10780. Brier scores also rise for both models on both sources. MIT ECE/Brier and every calibration bin were independently recomputed from saved probabilities; INCART calibration is reported from saved results, while its per-patient confusion matrices were checked and summed to the aggregate matrix.

**Decision:** retain CE selection as the current development reference. Do not select a model from the INCART results or claim that longer training/macro selection solved domain shift. Only 15 validation F beats makes macro selection unstable; larger representative validation cohorts and improvements to representation/loss require a new frozen experiment. SVDB remains sealed.

The six parent allocations total **837 seconds (13.95 GPU-minutes)**, below the 78-minute allocation ceiling. Source, inputs and complete paired scores are preserved locally in `implementation/data/ecg_selection_20260930` and remotely in `/home/guykalat/codex_ecg_selection_20260930`.

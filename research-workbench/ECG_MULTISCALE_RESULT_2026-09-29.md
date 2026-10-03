# Project 3: compact multi-scale ECG comparison result

## Result in plain language

The [predeclared compact multi-scale arm](ECG_MULTISCALE_COMPARISON_PROTOCOL_2026-09-29.md) did **not** improve the current window-centered CNN development reference. Four-class macro F1 fell from **0.634 to 0.614** on the inspected MIT-BIH candidate-A split and from **0.402 to 0.394** on the already-used INCART development source. The new model recovered 8/219 INCART fusion (`F`) beats, but called another **1,698 non-F beats** F, for only **0.47% F precision**. It recovered 30/1,958 INCART supraventricular (`S`) beats, versus 214/1,958 for the centered reference. Keep the simpler centered CNN as the current development reference; do not claim a multi-scale gain from this run.

| Metric | Centered CNN, 9,188 parameters | Multi-scale + channel gate, 29,580 parameters |
| --- | ---: | ---: |
| Selected MIT-BIH validation cross entropy | 0.447 | **0.419** |
| MIT-BIH development macro F1 | **0.634** | 0.614 |
| MIT-BIH S precision / recall | 0.737 / **0.634** | **0.808** / 0.529 |
| MIT-BIH F recall | 0/384 | 0/384 |
| INCART development macro F1 | **0.402** | 0.394 |
| INCART S precision / recall | **0.0173 / 0.109** | 0.00198 / 0.0153 |
| INCART F precision / recall | 0 / 0 | 0.00469 / 0.0365 |
| INCART cross entropy | 0.617 | **0.515** |

The new model's lower selected validation cross entropy and lower INCART cross entropy did not translate into better four-class recognition. Its MIT-BIH V F1 was 0.839 versus the centered reference's 0.873; INCART V F1 was 0.663 versus 0.669. Both models have substantial rare-class failures, and the 8 INCART F hits are accompanied by too many false alarms to be useful evidence of solving F.

## Fixed method and provenance

The exact matched-context targets remained **69,842 train / 13,708 validation / 17,029 inspected MIT-BIH development-test** beats, with the same subject assignment, N/S/V/F mapping, one-second target-centered named-MLII input, training-only centered transform (`global_std=0.34301185886458335`), square-root class weights, seed, AdamW settings, batch size 256, 12 epochs, and lowest unweighted validation-cross-entropy checkpoint rule as the centered reference. The new architecture used parallel kernels 3/7/15, a compact convolution stack, and an eight-unit squeeze-and-excitation gate. It did not use past beats or RR intervals. The selected epoch was **6**. INCART inference used the same **175,777** eligible beats from **75 records / 32 patients** and no refitted transform or threshold.

Slurm job **21734422** completed with exit code 0 on one RTX 3090 in **52 seconds** of allocation time; the program measured **40.06 seconds**, with **137,237,504 peak GPU bytes**. Its synthetic forward/gradient preflight passed. The three frozen input manifest hashes matched the previous robustness job before submission, all six staged source/script files matched local SHA-256 values, and the saved checkpoint was reloaded for both development evaluations. The result file records runner SHA-256 `56462aa406157be862d6186c4cf94037494d4e8be10b9c1896990a75ca564e28`, split/context/INCART manifest hashes, metric tables, full confusion matrices, per-subject MIT-BIH and per-patient INCART breakdowns, calibration and runtime.

Artifacts: [machine result](implementation/ecg_multiscale_result_2026-09-29.json) SHA-256 `2b166c3fb54c6c90ebdafcb40690bc7d65a7fd61ad7e30618d5761dd156791f4`; [Slurm log](implementation/ecg_multiscale_slurm_21734422.log) SHA-256 `65e90be4da1aba9f977c6fa603803e026cee00ed716fbc8d3e9c99879fb7e587`; selected checkpoint in ignored local `implementation/data/mitdb/multiscale_run_2026-09-29/multiscale_best.pt` and the remote run directory, SHA-256 `2b10ae13d2308336d74033d8d832812e6f94c585318ad296759800dc2c8bc13c`. Retrieved hashes matched the cluster. A separate local calculation from the saved confusion matrices reproduced both macro F1 values and the class support/precision/recall/F1 values, and checked 7 MIT-BIH subject groups and 32 INCART patients.

## Interpretation and next step

This is a **development** comparison. MIT-BIH candidate A and INCART were inspected before this architecture was chosen; neither is a fresh confirmation set. The lowered validation cross entropy alongside poorer development macro F1 also shows that checkpoint selection and the rare-class objective remain unsettled. A bigger attention model or sweep is not warranted by this one result. The next research step is a fixed, inexpensive error and signal-quality analysis of the centered reference, then a predeclared confidence-only versus quality/shift-aware abstention comparison. Assess candidate-B subject sensitivity before any broad generalization claim. Keep [SVDB reserved](ECG_FRESH_CONFIRMATION_SOURCE_2026-09-29.md) until the model and policy are frozen. These are annotated, centered beats, not real-time beat detection or a clinical monitoring system.

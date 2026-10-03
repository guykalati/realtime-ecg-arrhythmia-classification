# Project 3: first subject-disjoint ECG baseline result — 28 September 2026

## What ran

The [predeclared single-beat CNN control](ECG_BASELINE_RUN_PROPOSAL_2026-09-28.md) ran once on subject-disjoint candidate A. Slurm job **21719608** used one NVIDIA GeForce RTX 3090 under account `yshahar`, QoS `normal`, with a 30-minute wall cap. It completed successfully in **33 seconds** of allocated time; the Python pipeline recorded 24.35 seconds and a PyTorch allocated-memory peak of 69.3 MB (not total device usage). The job used the existing Python 3.11/PyTorch 2.5.1+cu124 environment without altering it.

The [trainer](implementation/ecg_baseline.py) used 360-sample MLII windows, training-only global mean/standard-deviation scaling, an unweighted three-block 1D CNN, AdamW, and 12 epochs. It selected **epoch 7** by lowest validation cross entropy (0.2986), then evaluated the held-out test once. The [full machine result](implementation/ecg_baseline_result_2026-09-28.json) includes every epoch, split/input hashes, confusion matrix, class metrics, and subject metrics. The result hashes match the local frozen [split](implementation/split_candidates/candidate_split_a.csv) and window manifest. The saved checkpoint and Slurm log are in the ignored local `implementation/data/mitdb/baseline_run_2026-09-28/` directory and remain on the cluster under `/home/guykalat/codex_ecg_baseline_20260928/output/`.

## Held-out result

On **17,043 beats from seven unseen subject groups**, accuracy was **94.10%** and four-class macro F1 was **0.4521**. The following class numbers are the more informative result.

| Class | Test beats | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| N | 15,101 | 0.949 | 1.000 | 0.974 |
| S | 429 | 1.000 | 0.002 | 0.005 |
| V | 1,129 | 0.830 | 0.830 | 0.830 |
| F | 384 | 0.000 | 0.000 | 0.000 |

The model correctly labeled **1/429 S** and **0/384 F** beats. It assigned 428 S beats to N and split F between N (193) and V (191). Thus the high accuracy mostly reflects the dominant N class; it does not demonstrate reliable rare-arrhythmia recognition. S precision of 1.000 is based on only one S prediction and is not evidence of useful S detection. Per-subject metrics are in the JSON; subjects with no rare class can show high macro F1 over their present classes and should not be interpreted as solving S/F.

This run used reference R-peak locations and half a second of post-peak signal. It is beat classification, not streaming detection or clinical decision support. The old course score used processed beat-level CSV splits and cannot be compared directly with this unseen-person test. MIT-BIH has only 43 groups in the primary scope, and validation contains just 15 F beats; estimates are unstable across subject assignments. No candidate B, five-class, external INCART, context model, or class-weighted rerun was submitted.

## Next comparison to approve separately

The first targeted change should address class imbalance while holding the **same single-beat input and split**: compare the unweighted control with a predeclared class-weighted loss, then assess whether neighboring-beat context adds benefit beyond that control. We have now examined candidate A's test errors, so later A results are **development comparisons**, not fresh untouched-test confirmation. Candidate B shares most test subjects with A and can assess sensitivity to which F-rich person is held out, but it is not independent confirmation either. A later external dataset or newly reserved subjects are needed for a genuinely fresh final test. The first run was far below the 30-minute cap, but this single observed runtime is not a guarantee for larger models. A future batch should freeze the weighting rule, exact context window, run count, selection metric, and GPU-hour ceiling before training.

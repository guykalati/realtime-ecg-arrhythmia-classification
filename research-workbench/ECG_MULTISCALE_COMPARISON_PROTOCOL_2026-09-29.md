# Project 3: frozen compact multi-scale development comparison

## Question and rationale

Test whether a compact multi-scale convolution plus channel gating helps recognize S/F beats beyond the existing window-centered weighted CNN. Multi-scale local features and channel attention are already published ECG ideas (see [paper review](ECG_PAPER_RESEARCH_2026-09-27.md)); this arm is a controlled paper-informed reference, not the claimed original contribution. Its result will tell us whether additional morphology capacity is worth carrying into the later shift-aware abstention study.

## Frozen input, selection, and reporting

- Use the exact candidate-A matched-context target manifest and four-class map, with 69,842 MIT-BIH train, 13,708 validation, and 17,029 already-inspected development-test beat targets. Feed only each target's one-second named-MLII waveform; discard saved prior-waveform and RR features. Subject assignments and all exclusions stay fixed.
- Use the existing **window-centered** transform: subtract each window median and divide by the standard deviation of centered *training* windows. Fit no validation, MIT-BIH test, or INCART constant. Use the exact class weights `sqrt(train_N/train_class)`, seed 20260928, batch 256, 12 epochs, AdamW learning rate 0.001 and weight decay 0.0001.
- Model: three parallel 1D convolution branches with kernel widths 3, 7, 15 and 16 channels each; concatenate, max-pool; a 48-to-64 kernel-5 convolution, max-pool; a 64-to-64 kernel-3 convolution; global average pooling; squeeze-and-excitation gate with reduction 8; four-logit linear head. No Transformer, neighboring beat, or RR input. Save the lowest **unweighted validation cross-entropy** checkpoint, exactly as for the centered CNN reference.
- Compare against the [saved centered reference](ECG_ROBUSTNESS_RESULT_2026-09-29.md) under the same training targets, selection rule and development sets. Report four-class macro F1 and N/S/V/F precision, recall, F1, support; confusion matrices; per-subject MIT-BIH and per-patient INCART spread; cross entropy, Brier and ECE; parameter count, peak GPU memory, and runtime. Evaluate the selected model on INCART with its fixed 175,777 four-class beat windows and 32 patients, with no external fitting.

## Decision boundary and cost

This is **one candidate architecture**, not a search. Preserve the centered CNN as reference even if the new model wins on one aggregate score. A useful improvement must show a coherent MIT-BIH validation/development and INCART error profile, especially S precision and F recall; there is no post-hoc score threshold that converts the inspected sets into confirmation. The proposed original extension remains the quality/shift-aware abstention comparison after this reference is measured.

Candidate B's alternative subject assignment is a later sensitivity analysis. This single job does not establish stability across rare-class subjects; an architecture claim remains provisional until that analysis and fresh source confirmation.

Use one RTX 3090, 2 CPUs, 8 GB RAM, at most 10 Slurm minutes; the old two-arm job completed in 55 seconds, while this 29,580-parameter feature extractor may take a few minutes. Stop the training loop at eight measured minutes, retain partial logs/checkpoints, and do not launch a sweep if this candidate is inconclusive. A CPU synthetic shape/gradient preflight and input-hash verification must pass before training begins. A cheaper alternative is to analyze existing centered-model error strata only; that would not answer whether paper-informed capacity changes the failures.

This remains annotated-reference-beat classification with a centered window including future waveform samples, not causal beat detection or monitoring. Candidate A and INCART are development data; reserve [SVDB](ECG_FRESH_CONFIRMATION_SOURCE_2026-09-29.md) for a later locked external check.

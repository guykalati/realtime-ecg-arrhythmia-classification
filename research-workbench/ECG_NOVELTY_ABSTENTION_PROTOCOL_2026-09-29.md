# Project 3: frozen confidence versus novelty-aware abstention comparison

## Question in plain language

When the centered CNN is unsure or sees an unfamiliar waveform, can it decline to label that beat while keeping more useful predictions than a confidence-only rule? This is a project-specific extension to the rebuilt ECG study, **not** a claim that abstention or embedding-distance detection is new in the literature. The previous [multi-scale architecture](ECG_MULTISCALE_RESULT_2026-09-29.md) did not improve the rare-class problem, so the saved centered CNN is the fixed classifier for this comparison.

## Fixed data and model

Load the existing centered CNN epoch-10 checkpoint, SHA-256 `d33678d4b77da35a03566e2c8e9cd43125b27f78ab2a2373af1df6f6eb989e15`. Do **not** retrain or fine-tune it. Use the same one-second, reference-beat-centered, named-MLII target waveform and four-class N/S/V/F mapping on MIT-BIH candidate A: 69,842 train, 13,708 validation, 17,029 previously inspected development-test beats. Apply its saved per-window median centering and training-only global scale. External development check: the already-used 175,777 INCART lead-II beat windows from 75 records / 32 patients. No INCART fit, thresholds, or checkpoint selection.

## Policies and selection

1. **Confidence baseline:** reject score `1 - max(softmax(logits))`. Lower means more trusted.
2. **Training-feature novelty:** take the centered CNN's 64-dimensional pooled feature vector before its linear head. Fit each feature's mean and standard deviation on **MIT-BIH training embeddings only**, with a small scale floor for zero-variance dimensions. A beat's novelty is its mean squared standardized feature distance. Convert it to a 0–1 empirical percentile against training distances, with ties handled by `searchsorted(..., side="right") / n_train`.
3. **Combined rule:** reject score `1 - max_probability + λ × novelty_percentile`, where λ is one of **0, 0.25, 0.5, 1.0**. λ=0 is the confidence baseline. Choose λ with the lowest mean selective **error** on MIT-BIH validation at target retained fractions 50%, 60%, 70%, 80%, 90%; ties choose smaller λ. For each fraction, retain the lowest-score `ceil(fraction × n)` validation beats. No label enters the training-feature fit. The selection uses validation labels only and is not a final test.
4. Save validation score cutoffs at retained fractions **50%, 70%, 90%** for each policy. Apply these exact cutoffs to MIT-BIH development and INCART without adjusting to their score distributions. Report the **actual** retained fraction and error among retained beats, plus N/S/V/F class-conditional retention and per-class precision/recall among accepted beats. Report all-beat confusion and the number rejected. A policy that simply rejects most S/F examples is not a success.

The main comparison is the validation-selected λ against λ=0. Save all four validation curves so selection is auditable; development data may be described but must not change λ. Include per-subject MIT-BIH and per-patient INCART retained fractions and selective errors. The reliability test is whether any apparent reduction in error persists without erasing S/F coverage, especially under INCART shift. Do not call any result clinical triage performance.

## Cost and limits

One RTX 3090 inference job with 2 CPUs, 8 GB RAM, a **10-minute Slurm cap**, and an 8-minute internal cap. The earlier full training/evaluation job took 52 seconds; this pass adds inference over training/validation/external sets and a small 64-feature fit, so several minutes should suffice. It creates no new model weights. A cheaper alternative is confidence-only abstention, but that cannot test whether training-feature novelty adds value. A larger classifier, kNN search over every training beat, or a quality-feature sweep is outside this fixed batch.

The MIT-BIH development split and INCART were inspected in earlier work. The MIT-BIH validation set contains only 15 F targets, so λ selection may be unstable for that class. Thresholds from validation may yield very different actual coverage on INCART. The subject and source differences, reference-beat centering, and use of future samples in the one-second window remain. Preserve [SVDB](ECG_FRESH_CONFIRMATION_SOURCE_2026-09-29.md) for one later locked check after deciding whether this policy deserves to be frozen.

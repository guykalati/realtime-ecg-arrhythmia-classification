# Timing ablation — completed, provisional improvement

Job **22001343** completed with exit0:0 on one RTX3090 in **307 allocated GPU seconds** (program302.14s), below the15-minute cap. All **18 runs** completed:two existing development splits × three seeds × waveform-only/timing-only/combined. Frozen source/data/feature/checkpoint hashes, support and confusion arithmetic, per-group matrix totals and12-epoch checkpoint/reloaded-validation checks passed. Raw result SHA-256: `7220a311009eaa948c664e2f520f590ca4e3674ed09c73389c7fa9e1d9001a2e`.

The new feature branch uses full annotation-stream preceding RR, a ratio to previous-ten-interval median and a missing-history flag. It replaces full-record normalization with past-only features, keeps the existing waveform embedding, initializes timing head weights at zero, and fits feature scale on MIT training only. This is a project-specific controlled adaptation of the cited method, not an established literature novelty.

## Means over six seed/split results

| Development source | Model | MacroF1 | S precision | S recall | S F1 | F recall | Brier |
|---|---|---:|---:|---:|---:|---:|---:|
| MIT | Waveform |0.557|0.518|0.525|0.429|0.000|0.115|
| MIT | Timing |0.349|0.016|0.005|0.007|0.000|0.197|
| MIT | Combined |0.584|0.442|0.707|0.484|0.002|0.105|
| INCART | Waveform |0.396|0.015|0.126|0.024|0.028|0.305|
| INCART | Timing |0.469|0.114|0.033|0.042|0.000|0.132|
| INCART | Combined |0.498|0.184|0.670|0.274|0.049|0.176|

These are averages of per-run metrics, not pooled confusion ratios or independent subject samples. MacroF1 and S F1 improve on both sources, mean F recall does not decrease and mean Brier improves, so the predeclared provisional reference-change rule passes. Combined-minus-waveform macroF1 is positive in **5/6 MIT comparisons** and **6/6 INCART comparisons**. MIT splitB/seed20260930 is worse by0.087. No statistical superiority claim follows from overlapping splits and reused INCART people.

## Material limitations

Fusion remains extremely weak:combined mean F recall is about0.18% on MIT and4.95% on INCART; INCART mean F precision is0.36%. Combined predicts on average2,757 non-F INCART beats as F. S improvement still comes with9,132 INCART non-S false positives on average; MIT mean S precision decreases. Timing-only's INCART macroF1 gain coexists with only3.3% S recall and zero F recall. Headline macroF1 cannot substitute for rare-class usefulness.

The combined model is a **provisional development reference**. Existing waveform checkpoints remain saved as controls. Annotation-assisted beat locations and centered1second windows require about0.5seconds future waveform. No evaluated R-peak detector or clinical monitor exists. No INCART fitting, EDB scoring or SVDB access occurred. The exact-input screen cannot settle cross-release person overlap.

Next: inspect per-subject/class errors; test a separately frozen subject-adversarial objective on the same morphology/timing input, monitor F suppression and calibration, and prepare synchronized-lead training artifacts before any lead-transfer pretraining. EDB requires its role/recording screen/grouping fixed before scores. Final confirmation remains separate.

[Protocol](ECG_RR_COMPARISON_PROTOCOL_2026-10-03.md) · [Audit](implementation/ecg_rr_compare_audit_2026-10-03.json) · [Primary-source rationale](ECG_NEXT_METHODS_RESEARCH_2026-10-03.md).

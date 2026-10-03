# Project 3: matched weighting and past-context comparison

## Result in plain language

On the same MIT-BIH targets and subject-disjoint candidate A split, **moderate class weighting improved minority-beat detection more than the tested past-context design**. The weighted single-beat arm had development-test macro F1 **0.555**, compared with **0.378** unweighted and **0.510** for weighted target-plus-two-prior-beat waveforms and RR intervals. The context arm reduced cross entropy but had lower macro F1 and accuracy than weighted single-beat. All arms remained weak on the rare fusion (`F`) class. This is development evidence: candidate A's test set had already been inspected in the earlier baseline.

| Arm | Macro F1 | Accuracy | S recall | V recall | F recall | Cross entropy | Brier | ECE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Single beat, unweighted | 0.378 | 0.914 | 0.000 | 0.428 | 0.000 | 0.358 | 0.134 | 0.030 |
| Single beat, weighted | **0.555** | **0.942** | **0.315** | **0.795** | 0.000 | 0.278 | **0.109** | **0.027** |
| Target + past two beats + RR, weighted | 0.510 | 0.925 | 0.284 | 0.793 | 0.016 | **0.250** | 0.123 | 0.031 |

The test supports were N=15,088, S=429, V=1,128, F=384. In the weighted single-beat arm, **135/429 S** and **897/1,128 V** were recovered, while **0/384 F** were. The context arm found **6/384 F** and predicted 27 normal beats as F. S and F are strongly concentrated in specific held-out subjects: 383/429 S occur in subject 209 and 372/384 F in subject 208. Per-subject metrics and confusion matrices are in the [machine result](implementation/ecg_context_comparison_result_2026-09-28.json); aggregate macro F1 should not be read as stable generalization across subjects.

## Frozen method and execution

The [context builder](implementation/mitdb_past_context.py) requires the target and two immediately preceding saved beat windows within one record, with positive preceding RR intervals. This excludes 88 first or second windows, leaving **100,579 targets**: 69,842 train, 13,708 validation, 17,029 test. The [frozen target manifest](implementation/past_context_a.csv) and [summary](implementation/past_context_a_summary.json) record the exact inputs and class counts. All three arms use these same targets. The first two arms see only the target's one-second waveform; the third also sees two prior beat-centered waveforms and two RR intervals. The [trainer](implementation/ecg_context_compare.py) fits waveform scaling from training targets and RR scaling from training RR values only. Class weights are `sqrt(train_N/train_class)` (N 1.00, S 5.65, V 3.58, F 12.46). Every arm has the same seed, 12 epochs, batch size 256, AdamW settings, and checkpoint rule: lowest **unweighted validation cross entropy**.

The [single Slurm job](implementation/run_ecg_context_compare.sbatch), ID **21723859**, completed with exit code 0 on an RTX 3090 in **1 minute 17 seconds** wall time (67 seconds measured within Python), below the 10-minute cap. Local and remote hashes matched before submission. Parameters were 9,188 for either single-beat arm and 9,420 for the context arm. Selected epochs were 5, 10, and 11 respectively.

## Interpretation and limits

The earlier baseline's 0.452 macro F1 used 100,667 targets; its score is not a matched-arm comparison with this 100,579-target experiment. The new arms isolate the tested weighting and context choices better, but selection on validation and prior inspection of candidate A test results limit confirmatory claims. No external INCART test was run.

These are **beat-centered windows**, not a proven real-time detector: each target waveform includes roughly 0.5 seconds after the R peak. Also, **5,609/100,579** nearest-prior RR intervals are under 0.5 seconds, so some preceding beat-centered windows can include signal after the target R peak. The context indices themselves never point to a later beat. A strictly causal experiment would need a separately specified waveform cutoff or target restriction; it is not established by this run.

**Existing-result failure audit:** The [saved per-subject confusion matrices](implementation/ecg_context_comparison_result_2026-09-28.json) show that 372 of 384 test F beats belong to subject 208. The weighted single-beat arm classifies those 372 as 233 N, 1 S, and 138 V, with **zero F**. The context arm moves many to V (71 N, 295 V) and detects only **6 F**. In subject 209, which has 383 of 429 test S beats, weighting recovers 135 S, while the context arm recovers 122. No other held-out subject gains a true S detection in either weighted arm. The training and validation splits contain only 403 and 15 F targets respectively, versus 384 in test. These counts make the current F result a subject-specific failure and leave little validation evidence for choosing an F-sensitive checkpoint. They do not identify the cause: possible class imbalance, morphology overlap, split composition, and model design need a controlled follow-up.

The strongest supported next direction is to retain the weighted single-beat arm as the current development reference, investigate the F failure and subject concentration, and design a genuinely untouched subject/external confirmation before claiming improvement. Any new sampling, model, or larger GPU run is a separate decision.

# Project 3: proposed imbalance and rhythm-context comparison

The first [subject-disjoint baseline](ECG_BASELINE_RESULT_2026-09-28.md) detected 1/429 S and 0/384 F beats. This proposal isolates two possible improvements: moderate class weighting and short **past-only** rhythm context. It is a development comparison, not a claim of clinical performance or a new untouched test.

## Frozen design before any run

Use the same 44 nonpaced MIT-BIH records, AAMI-style N/S/V/F mapping, and candidate-A subject groups. Keep the original one-second raw mV windows and train-only amplitude scaling. For every target beat, require two preceding beat windows within the same recording; remove targets without two predecessors from **all three arms**, then publish the revised train/validation/test counts before fitting. No labels, future beats, or future RR intervals enter model inputs. This requires reference beat locations and is not an end-to-end live detector.

Run exactly three arms with seed `20260928`, 12 epochs, batch 256, AdamW `lr=0.001` and weight decay `0.0001`, one checkpoint per arm selected by **lowest unweighted validation cross entropy**. This common selection rule avoids choosing a model based on the 15 validation F beats alone. Macro F1 and S/F recall are reported but do not decide the checkpoint.

1. **Matched unweighted control:** the same 1-channel CNN, retrained on the revised target set.
2. **Weighted single beat:** identical model/input with class weights `sqrt(n_N/n_c)` calculated from the revised **training** counts only. On the original A training counts this would be approximately N 1.00, S 5.65, V 3.58, F 12.47. The rule is fixed; no weight sweep.
3. **Weighted past-context model:** the same three-block CNN with three waveform channels (target and two preceding beats), plus two preceding RR intervals in seconds, standardized using training intervals only and joined to the pooled features before the final classifier. Use the same class-weight rule as arm 2. This isolates the extra context after accounting for imbalance.

Report the same validation and candidate-A development metrics for all arms: macro F1, per-class precision/recall/F1, confusion matrix, multiclass Brier score and 10-bin equal-width confidence calibration error, per-subject counts, parameter count, elapsed time, and GPU peak. The original candidate-A test has already been viewed and is **development evidence** for this next comparison. Candidate B shares most A test subjects, so it can probe the 208-versus-213 F-rich-person sensitivity but cannot serve as independent confirmation. Reserve any external INCART evaluation for a later, separately mapped protocol after model selection.

## Budget, alternatives, and limits

Submit **one RTX 3090 job** running the three fixed arms sequentially, with a 10-minute wall cap, 8 GB host RAM, and no automatic retry or sweep: at most **1/6 allocated GPU-hour**. Reuse the staged ~158 MB windows; generate context indices from the saved manifest, without another data download. Allow up to 1 GB of additional checkpoints/logs/cache. The first 12-epoch arm took 33 Slurm seconds, so 10 minutes is a generous cap for three arms plus context assembly, not a guarantee. Stop and report incomplete if the cap or memory limit is reached; do not silently change batch size or architecture.

A cheaper alternative is only arm 2, which tests whether weighting fixes the immediate S/F failure but does not address rhythm context. A more expensive alternative is grouped cross-validation plus an external dataset; that is more convincing scientifically and should follow only after this controlled development comparison. The [paper review](ECG_PAPER_RESEARCH_2026-09-27.md) documents later multi-beat and patient-wise work, so multi-beat context alone must not be claimed as novel. A later Guy-owned addition could test **shift-aware abstention** against confidence-only abstention, with external validation and explicit risk-versus-coverage metrics.

**Completion update, 28 September:** Guy approved the frozen three-arm batch. The target manifest and code were checked, then Slurm job 21723859 completed successfully. See the [results and causal-timing caveat](ECG_CONTEXT_COMPARISON_RESULT_2026-09-28.md). The context indices refer only to preceding beats, but beat-centered waveform windows can overlap the target time; this run does not establish a strictly past-signal model.

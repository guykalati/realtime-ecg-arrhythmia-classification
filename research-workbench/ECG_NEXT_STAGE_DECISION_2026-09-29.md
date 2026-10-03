# Project 3: next scientific stage after the matched context comparison

## What we learned

The original course notebook is deep learning on a one-dimensional ECG signal, not computer vision. Its beat-level Kaggle score does not establish performance on new people. The rebuilt raw MIT-BIH study does: in a subject-disjoint development split, class weighting raised four-class macro F1 to **0.555**, while the tested two-prior-beat context gave **0.510**. Neither solved fusion beats: the weighted single-beat model found **0/384 F**, and the context arm found **6/384 F**. These are development figures because candidate A's test set has already influenced subsequent choices.

The [paper lineage](ECG_PAPER_RESEARCH_2026-09-27.md) shows that multi-beat context and attention are already published ideas. Kachuee et al. are the data/task source for the old CSVs; the notebook's CAT-Net-like block is not a verified CAT-Net reproduction. Later work contributes compact hierarchical attention, patient-wise evaluation and external INCART tests, or multi-scale rhythm context. An honest personal contribution should combine a stricter evaluation with a clearly isolated new question, such as whether a quality or shift signal makes abstention safer for unfamiliar patients. It should not claim that attention or preceding beats alone are novel.

## Immediate decision: evaluate the data and failure before a larger model

The F class is only **15 beats in validation** for both candidate splits. Candidate B moves subject 208, which contributes **372/384** F test beats in A, into training; it keeps subject 209, which contributes **383/429** S test beats in A, in test. A/B therefore tests sensitivity to one influential patient but is not an independent final test. More architecture capacity cannot be credited with solving unseen-patient F detection from A alone.

The next bounded stage should be:

1. **Subject and label audit, no GPU:** quantify F and S counts by subject and record; inspect the source annotation symbols and raw waveform/lead availability for the largest error groups. Do not relabel or exclude difficult beats based on model errors. Save a fixed table and example identifiers for review.
2. **Fresh external data mapping, no training:** acquire the official INCART records with checksums, map its annotation symbols and named leads to the chosen N/S/V/F task, and identify its patient groups before preprocessing. Preserve an explicit `unmapped` count. This is a transport test, so never silently substitute a different three-class task for the four-class MIT-BIH task.
3. **Frozen model comparison after mapping:** retain the weighted single-beat CNN as a reference; compare one compact paper-inspired attention/multi-scale model under the same train-only scaling, class map, patient partitions, validation rule, and training budget. Include candidate B as sensitivity, then one external INCART result after model selection. Report macro F1, every class's precision/recall/support, per-person spread, calibration, and latency. A claimed improvement needs more than aggregate accuracy.
4. **Own extension only after the reference is stable:** compare confidence-only abstention with a predeclared quality/shift-aware score on the same held-out subjects. Report risk versus coverage overall and for S/F, and whether abstention disproportionately discards hard patients. This is a proposed research question, not a novelty claim or clinical alerting system.

## Cost and gates

The raw MIT-BIH core is about 94 MB and the existing matched three-arm job used an RTX 3090 for 77 seconds. The [INCART source](https://physionet.org/content/incartdb/1.0.0/) is much larger (about 563 MB compressed in the earlier inventory), and extracted windows plus provenance will use additional local/cluster storage; measure the actual footprint before training. The no-GPU audit is the cheap first step. A provisional architecture screen could cap each configuration at 10 minutes on one RTX 3090, then expand only if the data mapping and per-patient denominators are sound. Exact GPU-hours and final case counts are not known until the external mapping is built.

The next immediate work is the no-GPU audit and external mapping specification. An architecture sweep or large training batch should wait for its exact data count, model sizes, success rule, and cost estimate. The UI remains a later demonstration of a validated classifier and its uncertainty.

## Completed no-GPU label audit

The reproducible [audit script](implementation/ecg_subject_label_audit.py) joined the raw eligible annotation manifest to the exact matched-context targets by subject and checked that no subject crosses splits. Its [43-subject result](implementation/ecg_subject_label_audit_2026-09-29.json) records input hashes, annotation symbols, record IDs, and N/S/V/F counts. Summed matched counts exactly reproduce the experiment's train/validation/test denominators.

The concentration is sharper than the aggregate class counts suggest. Subject **213 contributes 362/403 training F targets**, subject **223 contributes 14/15 validation F**, and subject **208 contributes 372/384 test F**. Those three people supply **748/802** F targets across the matched study. The dominant raw annotation is the literal fusion symbol `F` (for example, 373 raw events in 208 and 362 in 213); one 208 event was excluded by the saved window/context rules. Subject **232 contributes 1,381/1,962 training S**, while **209 contributes 383/429 test S**. This strongly limits how much the current experiment can tell us about unseen-person rare-class generalization. It does not explain the model's mistakes by itself.

## External-test completion update

The [metadata mapping](INCART_METADATA_MAPPING_RESULT_2026-09-29.md), [pre-score input contract](INCART_EXTERNAL_PROTOCOL_2026-09-29.md), and [first external result](ECG_INCART_EXTERNAL_RESULT_2026-09-29.md) now complete stages 2 and an initial frozen-model transport check from stage 3. The existing weighted CNN achieved only **0.233 four-class macro F1** on INCART and detected no F beats. INCART labels and scores are now visible, so any normalization or architecture changes evaluated on it are development experiments. The next model comparison must state that limitation and reserve new patients or another source for final confirmation.

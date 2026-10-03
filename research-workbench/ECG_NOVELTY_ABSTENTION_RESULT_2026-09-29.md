# Project 3: novelty-aware abstention result

The [fixed comparison](ECG_NOVELTY_ABSTENTION_PROTOCOL_2026-09-29.md) completed without retraining the centered CNN. Adding training-feature novelty reduced validation selective error, but the development results reveal uneven rejection of rare classes. It does not establish a reliable policy for new patients. Preserve this as a measured project extension; keep the centered classifier as the reference and defer freezing an abstention policy for SVDB.

The classifier's pooled 64-dimensional features supplied a diagonal standardized distance, fitted only on 69,842 MIT-BIH training beats. Validation selected novelty weight **0.25** from 0, 0.25, 0.5, 1.0: mean selective error across validation retained fractions 50/60/70/80/90% was **0.05063**, versus **0.05749** for confidence alone. Thresholds from the 13,708 validation beats were then applied unchanged to 17,029 inspected MIT-BIH development beats and 175,777 INCART beats. These datasets are development evidence, with only 15 F validation examples.

| Source / validation target | Confidence: actual coverage / error | Novelty: actual coverage / error | Confidence → novelty S retention | Confidence → novelty F retention |
| --- | --- | --- | --- | --- |
| MIT-BIH / 50% | 64.4% / 1.29% | 73.1% / 0.76% | 35.0% → 12.8% | 24.2% → 9.9% |
| MIT-BIH / 70% | 76.6% / 1.88% | 83.1% / 1.32% | 48.0% → 33.8% | 42.4% → 28.4% |
| MIT-BIH / 90% | 95.0% / 3.15% | 96.5% / 3.05% | 80.4% → 76.9% | 79.9% → 77.6% |
| INCART / 50% | 35.3% / 11.91% | 25.8% / 4.85% | 27.5% → 40.4% | 28.8% → 3.7% |
| INCART / 70% | 54.1% / 10.60% | 51.6% / 10.34% | 46.6% → 61.5% | 41.6% → 29.7% |
| INCART / 90% | 84.9% / 12.18% | 86.8% / 12.46% | 84.6% → 89.2% | 78.5% → 75.3% |

Error means the proportion of retained beats classified incorrectly. Class retention means the fraction of **all true beats of that class** kept; it is not recall. The two rules have different actual coverage, so these rows are not comparisons at equal retained workload. In particular, the large INCART error reduction at the 50% validation cutoff accompanies lower overall coverage and rejection of 211/219 F beats. On MIT-BIH, aggregate error improves while much more S/F evidence is rejected. The centered classifier itself detects no F beats, so abstention cannot create F recognition. This is insufficient evidence of minority-sensitive reliability or clinical benefit.

Slurm job **21734499** completed with exit code 0 in **16 seconds**, with 9.86 seconds measured in the evaluator and 40,537,088 peak GPU bytes. Checkpoint SHA-256 `d33678d4b77da35a03566e2c8e9cd43125b27f78ab2a2373af1df6f6eb989e15`, the input manifests, and five staged source/script files were verified. Full-classifier macro F1 reproduced the earlier centered reference exactly on both datasets (0.634028 and 0.402040). The [result JSON](implementation/ecg_novelty_abstention_result_2026-09-29.json) includes all validation candidates, frozen cutoffs, class retention and accepted confusion metrics, and per-subject/patient coverage and error. SHA-256: `9216356582a9f02ca433d8b8a473a70130b12791bee74fcbf4dad2e3fb1517e5`. The [Slurm log](implementation/ecg_novelty_abstention_slurm_21734499.log) hash is `2e9851fcab8b640f670bc0825edcc4cb6a59ae4d2c11b4cdbab421e26132a88c`.

Per-beat labels, probabilities, novelty percentiles and group IDs are saved in ignored local `implementation/data/mitdb/abstention_run_2026-09-29/scores.npz`, hash `a59df04588c310d5c0b5c36f380ec7e358613b16142f674ce11fdbde1d3c8b80`. Retrieved hashes matched the cluster. An independent local NumPy calculation from those arrays reproduced validation selection, retained counts, errors and every class-retention count for all reported cutoffs. No further GPU evaluation was needed for verification.

Next: resolve the scarce and concentrated S/F training/validation evidence and test subject-split sensitivity before adding more policy parameters. Any later class-aware policy must prespecify both error and minority retention objectives. [SVDB remains reserved](ECG_FRESH_CONFIRMATION_SOURCE_2026-09-29.md). The study still classifies annotated, centered beats; it does not validate causal detection or monitoring.

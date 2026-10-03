# Longer ECG batch — verified 30 September 2026

All 12 frozen cells completed 100 epochs with exit code 0. Source/batch/checkpoint hashes and lowest-unweighted-validation-CE checkpoint selection passed audit. Saved MIT-BIH validation/development probabilities independently reproduced overall and per-subject confusion matrices, class metrics and cross entropy. INCART aggregate class metrics were checked against its saved confusion matrices; external inference was not rerun.

| Split / architecture | MIT development macro F1, mean ± SD | INCART macro F1, mean ± SD | INCART S precision / recall, mean | INCART F precision / recall, mean |
| --- | ---: | ---: | ---: | ---: |
| a_cnn | 0.5781 ± 0.0163 | 0.3945 ± 0.0037 | 0.0197 / 0.2766 | 0.0173 / 0.0091 |
| a_multiscale | 0.5965 ± 0.0251 | 0.4034 ± 0.0181 | 0.0110 / 0.0713 | 0.0035 / 0.0533 |
| b_cnn | 0.5426 ± 0.0807 | 0.3901 ± 0.0078 | 0.0174 / 0.1382 | 0.0072 / 0.3227 |
| b_multiscale | 0.4664 ± 0.0491 | 0.4116 ± 0.0056 | 0.0281 / 0.0717 | 0.0069 / 0.2618 |

Longer optimization did not reliably improve the retained 12-epoch centered-CNN development reference (MIT 0.6340, INCART 0.4020, one earlier seed). That earlier reference is not a matched three-seed estimate, so this comparison is descriptive. Multi-scale split A had mean INCART 0.4034, but substantial seed variation; its highest single seed is not the batch conclusion.

The split-B models detect more external F beats, but mean F precision remains below 1%. Improved recall therefore accompanies many false positives. S precision remains poor across arms. The split changes which influential people supply the training/test rare-class examples; there are not enough independent rare-class patients to infer a robust architecture gain from these beat counts. Both MIT development and INCART remain development evidence; SVDB stays unopened.

A cheap follow-up diagnosis from saved epoch histories shows that lowest unweighted CE and highest validation macro F1 choose different epochs in 10/12 cells. This does not prove that another criterion improves external performance: only CE-selected checkpoints were saved. It identifies a specific selection tradeoff worth a separately fixed comparison, especially with just 15 F validation beats. Longer training alone is not the recommended next change.

No new deployment or confirmation claim is made. Retain all seeds/splits, class precision/recall, source limitations and prior abstention findings.

Evidence: [protocol](LARGER_BATCH_PROTOCOL_2026-09-29.md), [all cells and group statistics](implementation/longrun_audit_2026-09-30.json), [independent audit script](implementation/audit_longruns_2026-09-30.py), [retrieval hashes](implementation/longrun_retrieval_hashes_2026-09-30.json), [Slurm accounting](implementation/longrun_slurm_accounting_2026-09-30.txt). Raw selected checkpoints, probabilities and epoch histories are in ignored `implementation/data/longruns_20260930/ecg/`.

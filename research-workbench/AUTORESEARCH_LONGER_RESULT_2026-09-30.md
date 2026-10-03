# Longer language-model batch — verified 30 September 2026

All nine Slurm cells completed with exit code 0. Candidate/source/data-manifest/checkpoint hashes matched the frozen contract. Each checkpoint was independently reloaded and rescored by the pinned GPU verifier during its job; the retrieved verifier records and hashes passed the local audit. Validation scored 2,097,152 byte targets per cell.

| Configuration | Parameters | Mean validation bpb ± sample SD | Range | Mean steps |
| --- | ---: | ---: | ---: | ---: |
| baseline | 1,711,104 | 0.957769 ± 0.005475 | 0.954447–0.964088 | 117,231 |
| lower_lr | 1,711,104 | 1.069177 ± 0.010375 | 1.057619–1.077685 | 118,808 |
| larger | 7,295,232 | 0.914496 ± 0.002000 | 0.912188–0.915740 | 35,678 |

The larger model reduced mean validation bpb by 4.52% versus the smaller baseline at the same 1,200-second training limit, despite completing fewer steps. It was better in all three paired seeds. Lower learning rate worsened all three seeds. This is a fixed-time, RTX 3090 development comparison, not an equal-step/equal-FLOP experiment or a sealed-test result. Three seeds describe variability; they do not establish broad statistical or task-level generalization.

The old five-minute batch remains a separate exhausted ledger. Do not attribute five-to-twenty-minute changes purely to architecture. The new nine-run ledger is now exhausted with all outcomes recorded; further runs require a fresh bounded contract under the existing user authorization.

This batch validates the training/evaluation workflow and provides development history. It does not measure an autonomous research agent or a benefit from retrieving prior experiments. The next engineering task is the bounded candidate-proposal loop, with fixed preparation/evaluator files and independently checked candidate outputs.

Evidence: [frozen protocol](LARGER_BATCH_PROTOCOL_2026-09-29.md), [local audit](implementation/longrun_audit_2026-09-30.json), [audit script](implementation/audit_longruns_2026-09-30.py), [ledger](implementation/autoresearch_longrun_20260929/results.jsonl), [retrieval hashes](implementation/longrun_retrieval_hashes_2026-09-30.json), [Slurm accounting](implementation/longrun_slurm_accounting_2026-09-30.txt). Raw checkpoints and verifier records are in ignored `implementation/data/longruns_20260930/language_model/`.

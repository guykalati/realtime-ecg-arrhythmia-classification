# Cluster resume handoff — resolved 30 September 2026

**Resolved:** SSH key authentication restored. Both arrays completed; all 21 cell outputs were retrieved and audited. See `AUTORESEARCH_LONGER_RESULT_2026-09-30.md`, `ECG_LONGER_RESULT_2026-09-30.md`, and `implementation/longrun_audit_2026-09-30.json`. The original handoff below is retained as history; do not resubmit these arrays.

Guy reported no cluster access today. No cluster connection or new GPU submission was attempted in this session. The two previously submitted arrays have not been cancelled; their current status is unknown until access is restored. Do not resubmit them before checking Slurm and saved outputs.

## Previously submitted, fixed batches

- ECG job **21734848**: remote `/home/guykalat/codex_ecg_longrun_20260929`; 12 cells, split A/B × CNN/multi-scale × three seeds, 100 epochs each, one GPU at a time. Outputs `output/<cell-id>/result.json`, `best.pt`, `history.json`, `validation_scores.npz`, `test_scores.npz`; preserve Slurm logs, including failed cells.
- Language model job **21734964**: remote `/home/guykalat/codex_autoresearch_longrun_20260929`; nine cells, baseline/lower learning rate/larger model × three seeds, 20 minutes each, one GPU at a time. Outputs `cells/<cell-id>/output/result.json`, `verified.json`, `model.pt`; preserve Slurm logs and failures. Record results in the existing new-batch ledger only after validating candidate/data/checkpoint hashes and independent rescoring.
- Maximum planned allocation across these batches was 354 GPU-minutes. This handoff authorizes no additional batch by itself; existing user authorization remains the task context.

## Retrieval and checks

1. Re-read the cluster skill and verify live SSH/Slurm access. Use `squeue` and `sacct` to establish every array cell outcome before considering retries. A missing result is not a completed or failed experiment without scheduler/log evidence.
2. Copy outputs into ignored local data storage, with a dated retrieval manifest. Do not alter historical checkpoint or source files.
3. ECG: validate batch/source hashes, actual 100-epoch completion, selected epoch, confusion-matrix counts and saved MIT per-beat probabilities. Summarize all seeds and both splits, including S/F precision/recall and subject-level variability. Both MIT development and INCART have already informed development; SVDB stays unopened.
4. Language model: validate each verifier record and checkpoint SHA, 2,097,152 scored validation targets, fixed candidate/data hashes, and training duration against the 1,210-second ledger tolerance. Record successful and failed attempts with actual evidence. Summarize seed mean/spread per configuration; do not claim retrieval-agent benefit from this model screen.
5. Compare the batch distributions with the retained prior development references. Do not pick a winning single seed or describe a 20-minute versus five-minute score change as an architecture-only effect.

The local inventory `implementation/longrun_local_inventory_2026-09-30.json` confirms 12 ECG and nine language-model configurations with no local frozen-source hash mismatches. It does not establish remote completion.

## Work available without cluster

The frozen public PMC acquisition is now complete: 977 verified XML documents, four excluded checksum mismatches, independent integrity/extraction QA, and sampled overlap rescoring passed. The fresh 20-article qualitative review is also complete. See `OFFLINE_PROGRESS_2026-09-30.md` and its linked artifacts. Neither acquisition nor these one-agent labels establishes final training eligibility. No project-1 GPU training has begun.

# Paired proposal-stage result

The frozen model/incumbent/memory/settings campaign produced four valid proposals using four generation requests, after recovery from a stopped local service. GET/tags-only failures from the initial campaign are retained separately; none sampled a proposal or started training. No extra proposal calls are planned from unused slots.

| Condition | Pair1 | Pair2 | Development history |
|---|---|---|---|
| No history | feed-forward1536→1920 | same source |0records|
| Retrieval | encoder layers4→6 | same source |11frozen development records|

The other architecture/training/evaluator settings remain identical. Temperature0.3, paired seeds20261001/20261002, training seed20260929. Arm order alternated by pair. Requests and model responses are preserved, and source/metadata/settings/history isolation passed local audit. AST protection and no-history isolation tests passed (2tests).

Both no-history hypotheses incorrectly call a higher bits/byte score an improvement. The executor retains the frozen **lower-is-better** criterion; hypotheses remain verbatim in artifacts. No metric direction or incumbent was changed.

Array21944594 has four20-minute training budgets within four22-minute allocations, two concurrent, with source/data hash preflight, isolated execution, causal/uniform evaluator checks and independent checkpoint reload. It is queued, so no trained result is available yet. The common development incumbent is0.9121882523777711bits/byte.

Because the candidate source repeats within each condition, the study compares two proposed configurations with timing replicates; it cannot demonstrate statistical retrieval superiority or varied independent architecture discovery. All outcomes will be retained.

Evidence: `implementation/paired_proposal_audit_2026-10-01.json`, proposal/recovery/GPU manifests and ignored raw request/response artifacts in `implementation/autoresearch_paired_recovery_20261001/`.

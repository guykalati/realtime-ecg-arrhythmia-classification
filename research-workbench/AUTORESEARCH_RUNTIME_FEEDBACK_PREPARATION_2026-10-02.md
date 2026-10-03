# Development-memory repair after paired results

The mutable proposer prompt now explicitly says **lower bits/byte is better**, refers to the common0.9121882523777711incumbent and explains the fixed-time cost of larger/deeper models. Earlier frozen campaign sources/prompts/results are intact. This addresses the two no-history hypotheses that incorrectly called higher bits/byte better; instruction compliance or training improvement has not been established by this edit.

A new development-only FTS index has17records:the prior2initial+9long-run+2pilot plus4paired outcomes. A separate derived paired-history ledger adds verified parameter counts, steps and improvement direction, distinguishing preemption from model-quality failure. Original17source records/ledgers are not overwritten. Counts/hash provenance are in `implementation/experiment_memory_runtime_manifest_2026-10-02.json`; index/raw derived file are ignored data artifacts.

Boundary/attention-divisibility/no-history-isolation tests passed (2tests). No proposal generation or GPU run followed this change. Retrieval/runtime-feedback benefit is unmeasured. A future comparison requires its own fixed matched protocol and fresh finite ledger; the four-candidate paired ledger remains exhausted. Do not count replayed or scheduler-interrupted attempts as improved architecture results.

The proposer also receives an exact static parameter profile for the protected byte model, computed without executing candidate code. Counts match the completed PyTorch models:reference7,295,232,widefeed-forward8,476,416,6layers10,844,160. This is model-specific parameter accounting, not a throughput/runtime forecast. Three boundary/isolation/observed-count tests passed. No new training result follows from adding the profile.

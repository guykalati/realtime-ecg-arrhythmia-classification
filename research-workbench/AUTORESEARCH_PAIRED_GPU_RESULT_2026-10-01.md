# Paired retrieval comparison: terminal result

| Trial | Condition | Outcome | Development bits/byte (lower better) |
|---|---|---|---:|
|1|No history|Preempted; restart refused existing output|—|
|1|Retrieval|Preempted; restart refused existing output|—|
|2|No history: feed-forward1920|Completed/independently reloaded|0.914782285|
|2|Retrieval:6layers|Completed/independently reloaded|0.931391109|
|Reference|Common incumbent|Previous verified same-seed development result|0.912188252|

**Keep the incumbent.** Both completed proposals were worse; the retrieval condition was worse in the single completed pair. This cannot establish that retrieval helps or harms generally: first-pair scheduler preemption, repeated candidate source per condition, two proposal seeds and fixed-time throughput limit the inference.

The completed no-history candidate trained32,237steps with8,476,416parameters; retrieval24,123steps with10,844,160parameters. Both used1200.04seconds onRTX3090. Frozen evaluator/source/data,2,097,152validation bytes and checkpoint hashes matched; remote independent reload reproduced each score and local artifact audit passed.

Full duplicate-inclusive Slurm accounting revealed initial15/95second preempted allocations for first-pair tasks, followed by1second automated restarts. Each restart found the preserved output directory and exited through the existing-output guard. Scheduler restart replaced prior stdout, so exact optimizer progress from preempted attempts is unavailable. Failure ledger conservatively charges the initial allocation duration; it is not measured training time. All6allocation attempts total2,558GPUseconds (42.63minutes), below88minutes. The four-candidate ledger is exhausted; no reruns were submitted.

For future batches, request `--no-requeue` and attempt-specific stdout, retaining interrupted artifacts. Do not overwrite output or silently extend a frozen ledger. Current source/preemption artifacts remain intact.

Evidence: `implementation/paired_gpu_result_audit_2026-10-01.json`, the four-entry campaign ledger and ignored retrieved logs/checkpoints/accounting at `implementation/data/paired_gpu_retrieved_20261001/`.

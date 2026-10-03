# Model-proposed experiment pilot

The local pinned Gemma4 12B QAT model received the current training source and explicitly retrieved development-ledger records. It had no execution tools. Exact replacements were checked against protected training/evaluation/provenance code before Bubblewrap execution with fixed data, seed and 1,200-second duration.

| Attempt | Proposed change | Outcome |
|---|---|---|
| 1 | Width384→512 with six attention heads | Rejected before GPU execution: width is not divisible by heads |
| 2 | Width384→480 with six heads | Completed Slurm21894420, independently verified .9666173553 bpb |

The second proposal received the first failure through development history. Its 9,854,784-parameter model ran 25,789 steps in 1,200.0667 seconds. The frozen width384, same-seed reference scored **.9121882524**. Candidate delta is **+.0544291029 bpb**, so the candidate is **discarded as an improvement**; all source, checkpoints and evidence remain preserved. Raw `configuration: larger` is an inherited label; authoritative identity is `agent_step2` and its candidate SHA256, not the unchanged reference architecture.

[Artifact audit](implementation/agent_pilot_audit_2026-09-30.json) passed source/data/checkpoint hashes, fixed seed/duration/byte coverage and agreement with the pinned independent GPU verifier. [The two-attempt ledger](implementation/autoresearch_agent_pilot_20260930/results.jsonl) is exhausted. The successful second attempt is the best *within this pilot*, but worse than the incumbent; those are separate comparisons. Its parent allocation was1,219 seconds, and the rejected first proposal consumed zero GPU allocation. Together with ECG selection, this bounded cluster batch used2,056 seconds (**34.27 GPU-minutes**), below its122-minute ceiling.

This implements a bounded local adaptation of the upstream [Karpathy autoresearch program](https://github.com/karpathy/autoresearch/blob/master/program.md): fixed preparation/evaluation, editable candidate, wall-clock training budget and keep/discard decisions. Our TinyStories byte task, RTX3090,20-minute budget, protected AST edits and immutable ledger differ from the upstream task and editing workflow. Development-memory retrieval and architecture feedback are the project addition. Their benefit remains **unmeasured** without matched runs with and without history. One adaptive validation seed is feasibility evidence, not a reliable model-quality estimate.

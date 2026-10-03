# Cached Qwen3B article-QA inference smoke

Job21919291 completed on one RTX3090, exit0:0, with41 allocated GPU-seconds. Model execution took33.36 seconds and peaked at6,351,469,056 allocated CUDA bytes (5.92GiB). The cached Qwen2.5-3B-Instruct snapshot aa8e72537993ba99e69dfaafa59ed015b17504d1 loaded in bf16 with transformers4.56.2 and torch2.5.1+cu124. No model download, training, SFT or continued pretraining occurred.

## Observed behavior

Four supported questions received source-consistent counts or sampling frequency:238 participants, ten patients,1kHz, and three Marfan patients plus four controls. Both unsupported endpoint questions received the prescribed abstention. **None of the four supported answers included the requested explicit exact supporting quote.** Base inference therefore works, while evidence-format compliance remains unmet.

These six cases were constructed and assessed by one agent for development. This is not a benchmark accuracy estimate, independent clinical validation, reproduction of the original QLoRA training or evidence that domain adaptation improves answers. Expected answers were not included in prompts. The three source articles are excluded from future training and independent QA testing via the development exclusion manifest.

The retrieval audit verifies source/case/manifest hashes, case coverage, context hashes and token caps. Compute recorded cached model-file hashes and matched safetensor hashes to LFS blob filenames; weights were not downloaded for a second local hash check. Greedy-generation warnings about unused sampling settings did not prevent execution.

Next: freeze a source-disjoint evaluation and training contract, address evidence quotation, then run a bounded compatibility/training smoke before a larger model comparison. Language-model loss alone is insufficient for article QA.

Evidence: [protocol](PMC_QA_BASELINE_SMOKE_PROTOCOL_2026-09-30.md), [audit and manual rubric](implementation/pmc_qa_baseline_smoke_audit_2026-09-30.json), [retrieval hashes](implementation/pmc_qa_baseline_retrieval_hashes_2026-09-30.json), [cases](implementation/pmc_qa_development_cases_2026-09-30.jsonl), [development exclusions](implementation/pmc_qa_development_exclusions_2026-09-30.json).

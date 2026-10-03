# Structured Qwen3B evidence-format development check

Cached Qwen2.5-3B-Instruct, the same snapshot/file hashes as the earlier smoke, ran the same six constructed development cases. The instruction now requests a two-field JSON object (`answer`, `evidence`) with an exact copied supporting quote, or a prescribed abstention and empty evidence. Maximum generation increased from128 to256 tokens. This changes instruction and output allowance together, so it does not isolate the effect of JSON alone.

All four supported answers were source-consistent and now include exact contiguous source quotations (previously0/4). Both unsupported questions still abstained semantically. However, only5/6 outputs parsed as the requested JSON schema. One unsupported output was plain text with an Evidence heading; the other returned JSON but omitted the required final period in the abstention string. **Neither unsupported output satisfied the complete strict abstention contract.** These failures are preserved, not silently normalized into successes.

Job21938144 completed with exit0:0 and46 allocated GPU-seconds. Script runtime35.11seconds, peak CUDA allocation6,355,090,432bytes. No training or model download occurred. The six cases have already informed prompt development and are not an independent benchmark; labels/answer judgments are single-agent development review. The three source articles remain excluded from training and independent QA testing.

The audit checks source/case hashes, cached-model hash agreement, ID/context coverage, token caps, JSON schema, exact source-quote substrings and strict abstention strings. Source-consistent answer content and semantic abstention are manual judgments, not automatic accuracy scores.

Next: validate output contracts at inference time and report format failures separately from unsupported claims; assess on newly frozen, source-disjoint questions before training comparisons. Do not treat an exact quote alone as proof it entails an answer. Do not report the current formatting check as a QA-model improvement benchmark.

[Audit](implementation/pmc_qa_evidence_audit_2026-10-01.json) · [Audit implementation](implementation/audit_pmc_qa_evidence.py) · [Frozen manifest](implementation/pmc_qa_evidence_manifest_2026-10-01.json)

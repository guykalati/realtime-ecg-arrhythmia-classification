# Remaining acquisition: audit and screening protocol

Purpose: verify all four completed source batches before measuring their discovery-corpus volume or overlap. No training or admission is authorized by these checks.

1. CPU audit21944638 depends on terminal acquisition array21944155. It checks frozen chunk-plan/source hashes, every successful XML MD5/SHA/byte count, extraction agreement and metadata identity, counts/failures and basic language/body flags. A pending predecessor21944634 was cancelled before executing to add its missing transitive import. Correction/source hashes are preserved.
2. CPU screen21944665 depends on **successful** audit21944638. It requires passed source audits with zero remaining items and matching frozen chunk-plan hashes before reading documents. It records input-document/audit hashes at execution. It compares successful documents with the old977 and first976 (known source SHA), then among all remaining chunks, using exact normalized DOI/body hashes. It screens only the frozen1000expert PubMedQA context texts using the existing five-token-shingle thresholds (≥30shared, Jaccard≥0.8 or context containment≥0.9); first10results are independently recomputed without the index. No questions or answers are provided.
3. Use the unchanged cached Qwen2.5-3B snapshot/tokenizer-file hashes, offline, to count title/abstract/section/body tokens without special tokens. This matches earlier raw-volume policy, including unresolved abstract/table/caption choices. Every output remains unreviewed.

Both stages: one CPU request, maximum10minutes each, noGPU. Audit2GBRAM, screen4GBRAM. No remote model download, classifier inference, split construction or continued pretraining. Admission still requires study/topic/full-text/retraction policy, further benchmark screening and source-disjoint train/evaluation decisions. Near-duplicate/paraphrase and cross-person identity claims are outside these checks.

Frozen manifests: `implementation/pmc_remaining_audit_manifest_2026-10-01.json` and `implementation/pmc_remaining_screen_manifest_2026-10-01.json`. Never substitute unfinished counts for verified acquired or admitted corpus volume.

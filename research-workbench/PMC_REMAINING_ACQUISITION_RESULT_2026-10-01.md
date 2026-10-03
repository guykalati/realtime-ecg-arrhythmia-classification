# Completed remaining acquisition and screening

Array21944155 completed all four capped chunks:3,866successful documents and4MD5-mismatch failures, with0remaining. Every successful XML source/extraction/identity/basic-quality check passed in CPUaudit21944638. CPUoverlap/token job21944665 completed; local source-plan/output hashes, coverage and arithmetic passed audit.

Combined with1,953previously audited articles, the discovery pool contains **5,819distinct acquired articles,50,437,502raw cached-Qwen tokens** (50,018,175tokens from explicitly `en` documents). These are acquired/unreviewed volumes, not an admitted training dataset. The fresh20check remains separate and is not added here.

The new3,866documents contribute33,629,658tokens;3,838are explicitly `en`,28have other/missing/case-sensitive language flags,28have short-body flags and **5are XML retraction notices**. Flags may overlap. Retraction notices are not evidence-bearing training text; their linked articles need notice/relationship screening before admission. Metadata retraction status alone did not filter out notice documents.

No exact DOI/body duplicates were detected against old977, first976 or across the remaining batches. No overlap met the frozen1000expert PubMedQA context-shingle threshold; this does not exclude paraphrases, semantic overlap or other benchmark contamination. All documents remain unreviewed, with no training or automatic admission.

Evidence: `implementation/pmc_remaining_result_audit_2026-10-01.json`, frozen source/audit/screen manifests and ignored retrieved source-check/document/failure outputs. XML remains on the cluster. Remote source auditing and first10naive context checks were not independently rerun on the Mac.

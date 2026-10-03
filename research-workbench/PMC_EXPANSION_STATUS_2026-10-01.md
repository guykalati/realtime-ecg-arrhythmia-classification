# Biomedical expansion resumed after selected storage cleanup

Guy selected Reddit inventory groups1–3 for deletion. The exact Reddit data directory and two project-local cached models were removed; absence checks passed and the deletion record was retrieved locally. Reddit source/paper directories remain. Its project-directory allocation fell from238,796,700,672 to148,453,376 bytes: about238.65GB removed. Shared current models, older HW1/HW2 and portfolio run directories remain outside that deletion scope.

## Active finite jobs

- Metadata job21928731:5,000 new candidate articles, CPU only,100MB output/two-hour cap. Still running; not a completed5,000-article acquisition.
- Full-text job21937203:976 selected versions from the frozen first1,000 completed metadata attempts, CPU only, one-hour cap,1GB XML plus1GB extraction ceiling. Initial live check showed22 checksum-verified/extracted articles. Complete results are pending.

All1,000 frozen metadata attempts succeeded.22 articles lack required DOI/PMID identity and two have a retracted/unknown version flag; these24 are excluded from this full-text batch. Exact-version CC BY/CC0 licensing and source XML checksums are pinned. All1,000 expert PubMedQA PMIDs and three constructed QA development articles/IDs/DOIs are excluded before acquisition. This does not replace later context-overlap, XML identity/language/retraction, topical/design and full-body quality checks.

Source scripts and inputs were checksum-verified remotely before submission. Outputs remain unreviewed, and no new training corpus or model improvement is claimed. Full XML stays on the cluster; manifests, audits and small reports stay local. The original977-article local corpus is not replaced.

A fresh20-article screen sample was frozen before inspecting its article contents or model outputs. It will test the repaired prompt on unseen development cases; independent expert accuracy still requires independent labels. Sampling seed20261002 is an identifier and does not change the1 October execution date.

Evidence: [XML plan](implementation/pmc_large_xml_plan_2026-10-01.json), [fresh screen plan](implementation/pmc_fresh_screen_plan_2026-10-01.json), [deletion record](cluster-storage-review/deletion_2026-10-01.json), [prior inventory](cluster-storage-review/INVENTORY_2026-10-01.md).

Next: retrieve terminal summaries/accounting and audit complete record coverage, source hashes, exact extracted text and identifiers. Then review the fresh sample and filter corpus tiers before tokenization or bounded QLoRA/continued-pretraining experiments. Larger agent/ECG trials retain their own finite protocol requirements.

## Verified completion update

Job21937203 completed976/976 downloads and extractions, zero failures,122,216,074 XML bytes and37,566,448 extracted-document bytes. Independent re-reading passed source/checksum/extraction/identifier auditing;972 English and four other-language articles, eight short-body flags. These flags remain outside any automatic admission.

The fixed five-token-shingle PubMedQA-context screen found zero matches at the original thresholds (at least30 shared, Jaccard≥.8 or context containment≥.9). Ten direct-set rescoring checks agreed with the indexed result. Exact DOI/body checks against the previous977 and within the new batch found zero duplicates. This does not exclude semantic/paraphrase leakage or other benchmarks.

CPU token job21938349 measured8,450,243 new tokens; old+new totals are1,953 distinct article IDs,16,807,844 tokens (16,672,527 English-tagged). These are volume counts, not approved training volume. The20 fresh review articles belong to the new976 and are not added twice. Raw XML remains on the cluster.

[Fresh screen result](PMC_FRESH_SCREEN_RESULT_2026-10-01.md) records five clear core candidates, one clear off-scope inclusion, two ambiguous-scope predicted inclusions and two unresolved cases. The classifier is triage only. The five source-reviewed candidates provide49,437 tokenizer-counted tokens but are not admitted by this count.

## Subsequent verified state

The5,000-row metadata acquisition completed (0failures) and passed the frozen audit. Remaining3,870eligible versions were frozen into four acquisition chunks, at most two concurrent (array21944155). First two chunks completed969/966documents with one MD5-mismatch failure each; final two chunks remain running. Dependent basic source/extraction/identity audit21944638 is scheduled for all four chunks. No extra tokens or admitted-training volume are claimed until terminal auditing/overlap/volume checks complete.

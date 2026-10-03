# Remaining frozen5000 acquisition

The metadata batch completed5000/5000 with zero failures; hashes, ID order/coverage, byte counts and consistency of the first1000 snapshot passed audit. It includes5080 versions and19 articles with a retracted/unknown version flag. Exact-version licensing must be checked, not inferred from the discovery query.

The first1000 already yielded976 source-verified full texts. The remaining4000 metadata rows are partitioned into four fixed1000-row chunks. Selection rejects any retracted/unknown version, any reserved development/PubMedQA ID across versions, missing identity, unsuitable license or invalid source URL. The highest-numbered eligible CC BY/CC0 version is chosen. There are3870 selected versions and130 exclusions in this continuation. No source IDs overlap between chunks or with the first1000.

Four CPU allocations, at most two concurrent, one requested CPU/2GB RAM per job,60-minute ceiling each; zero GPU. XML and extracted text are each capped1GB per chunk (8GB aggregate worst-case), with internal time/byte stops and explicit partial summaries. Actual expected volume based on the earlier1000 is around half a gigabyte of XML, plus extracted text; time is likely tens of minutes per pair plus queue/service latency. The cheaper alternative is keeping the current1953 articles, which would not extend full-text acquisition from the already completed metadata batch.

Purpose is unreviewed acquisition and quality auditing, not admission or training. After completion, verify files/extraction/identifiers, language/body and publication-notice flags; compare exact duplicates and fixed benchmark contexts; then review topical/study tiers and freeze data/evaluation partitions. Quote-validation or metadata eligibility alone cannot admit documents.

All raw XML stays on the cluster. Source/version/exclusion/input hashes and finite budgets are frozen in the [manifest](implementation/pmc_remaining_xml_manifest_2026-10-01.json). The selected source list per chunk is preserved in staged plan.json files. No old corpus or run output is overwritten.

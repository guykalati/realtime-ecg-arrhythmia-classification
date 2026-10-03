# Project 1: study scope and exact benchmark-exclusion gate

The corpus audit now checks every known PMID across an article's downloaded metadata versions against the **1,000 expert-labeled PubMedQA article IDs**, pinned from the [official repository](https://github.com/pubmedqa/pubmedqa/tree/1cbae8e92f72f20c8d3747cbb3bf5bc53554d997). All expert articles are excluded from continued-pretraining candidates, including the expert train/development partitions, so a later explicit supervised benchmark workflow can have its own boundaries. Benchmark questions and answers were not used to create corpus targets or train a model.

The [exclusion manifest](implementation/pubmedqa_expert_exclusion_2026-09-29.json) contains IDs and source provenance only. Official source commit: `1cbae8e92f72f20c8d3747cbb3bf5bc53554d997`; `data/ori_pqal.json` SHA-256: `8b3276be8942ebbd77f3ddcda12c1749bf0e490045a736fd8438ee40cf37a41d`. The raw source is isolated in ignored data storage. The [updated audit](implementation/pmc_eligibility_audit.py) combines the frozen 1,000 metadata rows, the existing XML checks, all 40 qualitative article screens, the exclusion IDs and explicit study tiers. Prior audit artifacts were preserved; [new manifest](implementation/pmc_scope_benchmark_audit_2026-09-29.jsonl) and [summary](implementation/pmc_scope_benchmark_audit_2026-09-29.summary.json) record this stage.

| Gate in the frozen 1,000-article sample | Articles |
| --- | ---: |
| Licensed version candidates, no exact expert PMID match | 981 |
| Licensed version candidates with missing PMID | 15 |
| Excluded because any version was marked retracted | 4 |
| Exact expert PMID matches | 0 |

An absent match establishes only that no known metadata PMID matched this particular benchmark. Missing PMIDs remain unresolved. DOI identity, alternate publications, abstract/text near-duplicates and other evaluation datasets still need checks before training. This is a snapshot of the earlier downloaded metadata; it is not a fresh retraction lookup.

The 16 original-study candidates among the 40 screened documents now have explicit [study-type labels](implementation/pmc_study_tiers_2026-09-29.json): **6 human clinical empirical studies**, **2 human health-services studies**, **6 preclinical studies**, **1 veterinary study**, and **1 expert-consensus study**. These categories preserve differences in populations and evidence. They were assigned from the existing qualitative screens, with the human/consensus abstracts rechecked; they are one agent's development labels rather than independent domain adjudication. One preclinical candidate has no body in its selected XML and remains unusable as full text.

The [six-document primary review queue](implementation/pmc_primary_review_queue_2026-09-29.jsonl) requires a human clinical empirical label, the selected clean licensed version, well-formed JATS with a body, no exact expert PMID match and no duplicated DOI in this sample. These are research-literature documents about thrombosis, AF electrograms, cardiac biomarkers, TAVR prognosis, congenital-heart-disease diagnosis, and heart-failure outcomes. This queue is a review artifact, not approved training data. The health-services, preclinical, veterinary and consensus tiers remain available for a separately described broader literature task.

Two focused regression checks passed: version-specific licensing/article-level retraction handling, and benchmark PMID handling for integer/string IDs, missing IDs and matches found in an alternate version. The actual audit reproduced the existing 40-article structural confusion counts (14/9/2/15) and the new gate/tier totals. No additional article XML or model weights were downloaded; no training ran.

Next corpus work: audit the remaining frozen random XML articles under this taxonomy, then specify a fresh larger sample for automatic-screen validation; resolve missing identifiers and source completeness; perform DOI/text overlap and extraction QA; and measure article/token/storage volume before a bounded larger acquisition or model run. The 200,177-ID discovery pool is still not a ready training corpus.

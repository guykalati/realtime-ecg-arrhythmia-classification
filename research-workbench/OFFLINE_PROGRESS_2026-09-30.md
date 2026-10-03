# Offline progress — 30 September 2026

Guy reported that cluster access is unavailable today. This session continued the public-data and local validation work without attempting a cluster connection. The previously submitted GPU arrays were not cancelled or resubmitted. Their current outcomes remain unverified.

## Project 1: larger article corpus completed

Resumed the interrupted acquisition at 129 verified articles. Every one of the frozen 981 candidates now has a recorded outcome: **977 checksum-verified XML documents**, **four excluded checksum failures**. Storage is **121,150,288 bytes** (121.15 MB), below the 2 GB cap. The frozen contract retained version-specific CC BY/CC0 licensing, known PMID, article-level retraction metadata screening, and exclusion of all 1,000 expert PubMedQA IDs. It uses the earlier metadata snapshot, not a fresh retraction lookup.

The XML contains **4,709,894 body words**. Extracted paragraphs, tables and figure captions contain **4,647,381 whitespace-separated words**; these are not model-tokenizer counts. Paragraphs retain section paths and source version/checksum provenance. Bibliographies are excluded. Full source XML remains available separately. This is a quality corpus, **not approved training data**; no project-1 training ran.

| Quality observation | Count |
| --- | ---: |
| XML `research-article` | 680 |
| Other XML article types | 297 |
| English main XML language | 966 |
| Other main XML languages | 11 |
| Body shorter than 500 words | 9 |
| Duplicated DOI within this batch | 0 |
| Exact normalized body duplicates | 0 |
| PubMedQA context-overlap flags under frozen rule | 0 |

The other article types include reviews, case reports, letters, corrections and one retraction notice. The notice itself passed the earlier metadata retraction flag; its document type still requires exclusion from primary research evidence. XML type alone cannot establish substantive original study eligibility.

All four source failures were MD5 mismatches: PMC11142952.1, PMC11571354.2, PMC11942725.1 and PMC7338754.1. Changed bytes were rejected. A second request for the first item returned an object whose ETag matched its observed bytes but differed from the frozen expected checksum. The cause of the change is not established; none of these versions entered extraction or review queues. The downloader now records such failures and continues, while preserving fatal cap/contract errors.

The text-overlap rule uses normalized five-token shingles, at least 30 shared shingles, and either Jaccard ≥ .80 or benchmark-context containment ≥ .90. Only expert benchmark contexts and IDs are used; benchmark questions and answers are not corpus targets. Zero flags is limited to this benchmark and these thresholds. It does not rule out paraphrases, short overlaps, other benchmarks, or pre-existing backbone contamination.

Independent local QA rechecked all 977 saved MD5/SHA-256 hashes and sizes, complete coverage of successful/failed planned IDs, paragraph/figure/table counts, abstract extraction, and duplicate totals. A separate naive set-intersection implementation reproduced the overlap screen on 20 randomly selected documents. Three focused regression checks passed, including section/table preservation and bibliography exclusion. No body-bearing document had extracted word coverage below 80%; the lowest ratio, 80.07% in PMC12330163, reflects unusually long heading/supplementary-title content. Supplementary files themselves were not downloaded. Source citation placeholders and non-paragraph material still need cleaning/review before training.

### Fresh qualitative development review

A separately frozen random sample of 20 articles was drawn from the 887 candidates outside the original XML pilot, with seed 20260930. All 20 were reviewed using their titles, abstracts, XML types and body availability. **11/20** had a central cardiovascular question; **7/20** were provisional human empirical cardiovascular study candidates. These are one-agent development labels, not independent clinical adjudication or full-text critical appraisal. Rheumatoid-arthritis comorbidity and sports-performance studies were treated as borderline scope cases and retained for later review.

Two provisional clinical candidates have Portuguese primary text and internally inconsistent reported percentages in their abstracts. They remain outside the English review queue. The Portuguese abbreviation “AF” in the sickle-cell study means *anemia falciforme*, not atrial fibrillation; this illustrates why abbreviation matching cannot define the corpus topic.

Combining the previously screened human studies with the fresh sample yields an **11-document English human empirical review queue**, containing **51,735 XML body words**, after body/language/duplicate/benchmark checks. This is a review artifact, not a training release. Wider preclinical, health-services and review tiers should retain their own evidence labels. The 200,177-ID discovery pool remains unvalidated.

Evidence: [acquisition summary](implementation/pmc_expansion_summary_2026-09-30.json), [excluded versions](implementation/pmc_expansion_source_failures_2026-09-30.jsonl), [independent QA](implementation/pmc_expansion_qa_2026-09-30.json), [fresh review plan](implementation/pmc_expansion_review_plan_2026-09-30.json), [review reasons](implementation/pmc_expansion_review_labels_2026-09-30.jsonl), [English review queue](implementation/pmc_primary_review_queue_2026-09-30.jsonl), and [provenance hashes](implementation/pmc_expansion_provenance_2026-09-30.json). Large XML/text outputs are in ignored `implementation/data/pmc_xml_expansion_20260929/` storage.

## Projects 2 and 3: cluster results need retrieval

The local frozen-source inventory passed without hash mismatches. It confirms the intended configurations, not the remote outcomes:

- **Project 2, job 21734964:** nine TinyStories runs, baseline/lower learning rate/larger model across three seeds, with 20 minutes of training per cell and independent checkpoint rescoring. The repair-agent evaluator also depends on cluster CPU. No new repair evaluation or verified longer-run result is available locally.
- **Project 3, job 21734848:** 12 ECG runs, two architectures × two patient splits × three seeds, with 100 epochs per cell. Longer-run results and checkpoints have not been retrieved. Earlier centered-CNN development results remain the retained reference; no new winner is claimed. SVDB remains unopened.

The [cluster resume handoff](CLUSTER_RESUME_HANDOFF_2026-09-30.md) gives remote directories, output paths and validation steps. Once access returns, first inspect Slurm/accounting and artifacts, retrieve all successes and failures, independently validate the scores, then compare seed/split distributions. Do not repeat the batches merely because local outputs are absent.

Local work on this fixed acquisition and review batch is complete. GPU-result collection, evaluation and further cluster training wait for restored access. No other user decision is required at this stopping point. Wayfinder remains deferred.

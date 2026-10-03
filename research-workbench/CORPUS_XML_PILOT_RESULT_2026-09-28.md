# Project 1: 100-article XML quality pilot

## Result in plain language

The frozen pilot retrieved **100/100 licensed PMC XML files** (80 random candidate articles and 20 deliberately selected metadata edge cases). All were well formed JATS `<article>` documents, and an independent local check matched every recorded byte count and MD5. The transfer was **11,272,324 bytes**, far below the 250 MB cap. This confirms that the retrieval and parsing route works. It does **not** confirm that the 200,177-ID search pool is a clean cardiovascular original-research corpus.

In the 80-article random subset, all XML records declare English, 77 have an abstract, 79 have a `<body>`, and 76 have more than 1,000 extracted body words. The median extracted body length is 4,567.5 words. XML article types are 49 `research-article`, 18 `review-article`, 9 `case-report`, and one each of `other`, `correction`, `brief-report`, and `abstract`. A `research-article` tag is not sufficient by itself: one manually reviewed article with that tag is a 511-word single-patient case narrative.

## Manual topical screen

The 20 preselected random articles marked for manual inspection were screened from their titles, abstracts, XML article types, and body structure using these rules:

- **Central cardiovascular relevance:** the main question concerns the heart, cardiovascular system, vascular disease, blood pressure, cardiac arrest, or thrombosis. Merely mentioning cardiovascular disease as one risk, comorbidity, or possible consequence is insufficient.
- **Strict original-research candidate:** central relevance plus a substantive original study, rather than a review, case report, opinion, or short case narrative.

Eleven of 20 were judged centrally relevant; **six of 20** met the stricter original-research screen. The [article-by-article decisions](implementation/pmc_xml_manual_review_2026-09-28.jsonl) include reasons. Approximate Wilson 95% intervals are 34–74% for central relevance and 15–52% for strict eligibility. Those are wide because only 20 random articles received human topical labels. The 20 deliberately selected edge cases are **excluded** from both denominators. This is one nonexpert reviewer, not an adjudicated clinical literature screen; the six are candidates, not finalized inclusion decisions.

## Edge-case checks

The 20 targeted articles include all four retracted articles from the 1,000-ID metadata sample, nine manuscript-version cases, six articles with another-license version, five missing-DOI cases, and one missing-PMID case; categories overlap. Their selected XML files were structurally parseable. This does not make them eligible. Retracted articles remain excluded at article level, and a selected licensed version does not license a different version. The [frozen plan](implementation/pmc_xml_sample_plan_2026-09-28.jsonl), [per-file checks](implementation/pmc_xml_checks_2026-09-28.jsonl), and [summary](implementation/pmc_xml_summary_2026-09-28.json) preserve the evidence; the downloaded XML is in the ignored local data directory.

## Decision implication

The broad query is useful for discovery but too noisy to become a training manifest unchanged. The next corpus design needs explicit document-type and cardiovascular-centrality rules, article-level retraction and version handling, DOI/text deduplication, and PubMedQA evaluation exclusion before bulk acquisition. The pilot shows the technical path is feasible and makes those quality gates measurable. It does not justify multiplying 6/20 by the full search count as a reliable final corpus size.

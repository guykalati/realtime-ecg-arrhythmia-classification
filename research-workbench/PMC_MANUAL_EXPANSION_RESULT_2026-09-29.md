# Project 1: expanded eligibility screen on the frozen XML sample

An additional 20 PMC articles were selected with seed `20260929` from the 60 previously unreviewed articles in the frozen 80-article random XML sample. The [plan](implementation/pmc_manual_expansion_plan_2026-09-29.json) was saved before review. One agent then read each selected title, abstract, XML type, and relevant body structure under the earlier central-cardiovascular and substantive-original-study rules. The [article-level labels and reasons](implementation/pmc_manual_expansion_labels_2026-09-29.jsonl) are a qualitative development screen, **not** independent expert adjudication. No new XML was downloaded, and no model was trained.

Across all **40** randomly selected, screened articles, **28/40** had a central cardiovascular question and **16/40** were substantive original-research candidates. Approximate Wilson 95% intervals are **55–82%** and **26–55%**, respectively. These are wide one-reviewer sample intervals, not estimates of the final eligible full corpus. At least one original candidate is unusable as full text because its selected JATS XML has only a front section and abstract.

The provisional rule “JATS `research-article` plus at least 1,000 body words” produced the following development comparison with those 40 qualitative labels:

| Structural queue | Original candidate | Not original candidate |
| --- | ---: | ---: |
| Queued | 14 | 9 |
| Not queued | 2 | 15 |

Thus the queue admitted **9/23** noneligible reviewed items and missed **2/16** original-study candidates. The misses are instructive: [PMC12136753](https://pmc.ncbi.nlm.nih.gov/articles/PMC12136753/) describes original cardiac experiments but its selected XML has no `<body>`, so it is a source-completeness problem; [PMC13089009](https://pmc.ncbi.nlm.nih.gov/articles/PMC13089009/) is a short but original Medicare cardiac-imaging analysis labeled `brief-report`. Noneligible queued examples include a uterine-surgery case series with cardiovascular extension as a complication, a height-loss study that uses cardiovascular disease only as background, and a literature review of emergency-call NLP labeled `research-article` in XML. This shows why neither title search nor XML type can serve as the final content gate.

The [audit script and summary](implementation/pmc_manual_expansion_audit.py) recompute the selection checks, counts, and intervals. Next, define corpus tiers before scaling metadata: human clinical original studies, preclinical mechanistic studies, veterinary work, and Delphi/consensus surveys answer different kinds of questions. Keep article-level retractions, exact-version license, usable body text, DOI/text deduplication, and benchmark overlap as separate gates. A higher quality validation set should use independent domain review and a fresh random sample; these 40 have now influenced filter design. The 200,177-ID manifest remains a discovery pool, not a training set.

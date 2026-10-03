# Fresh20 corpus-screen check

Twenty candidate IDs were frozen before article-content or model-output inspection. All20 source XMLs passed hashes, extraction equality, identifiers and English-language checks. Source-only labels were then frozen before classifier execution. The existing29-case prompt was reused **unchanged**; no fresh-case feedback was incorporated during this run. This improves the development comparison, but labels are still one agent's review of abstracts/opening methods, not independent expert adjudication.

## Agreement and unresolved cases

| Scope | TP | FP | TN | FN | Unresolved |
|---|---:|---:|---:|---:|---:|
|All20; uncertain scope treated outside primary core|5|3|10|0|2|
|16 clear-scope cases only|5|1|8|0|2|

All five clear cardiac human-study candidates were selected: cardiac pulse monitoring in Parkinson disease; cardiac deterioration/coronary disease in AML; coronary CTA/PET prognosis; childhood blood-pressure associations; and STEMI metabolomics (27 people,108 samples).

The clear false inclusion is PMC4856269:87 healthy men studied for inflammation/oxidative biomarkers. The model used background ischemic-heart-disease protection to call it a central cardiac study, although no primary cardiac endpoint was measured. This reproduces the background-versus-main-question failure.

Two additional predicted core positives concern scope ambiguity, not demonstrated invalid study design: PMC10860437 mixes sports injuries with cardiac catastrophes; PMC9503453 concerns metabolic-syndrome genetics. The source-only labels marked both uncertain. Scuba-death surveillance and broad elderly drug interactions were the other two uncertain-scope cases. Counts excluding these four are reported separately; ambiguity is not silently relabeled after model output.

PMC11335015 (apoB review) failed exact design quotes in both attempts. PMC13080820 (one infant with Noonan-related cardiomyopathy) failed exact topic quotes in both attempts. They remain unresolved rather than negative clinical-study labels. All model outputs remain triage records, **not training admission**. Quote validation does not establish entailment or topical accuracy.

## Decision

Do not use this classifier to automatically admit the expanded corpus. Preserve separate primary human-study, preclinical, review and case-report tiers; review proposed inclusions against source purpose/methods/results, especially topic evidence drawn from background. The fresh20 are now development cases and cannot provide an independent estimate for later prompt changes.

[Frozen source labels](implementation/pmc_fresh_screen_labels_2026-10-01.jsonl) · [Label freeze](implementation/pmc_fresh_screen_label_freeze_2026-10-01.json) · [Result](implementation/pmc_fresh_screen_summary_2026-10-01.json) · [Audit](implementation/pmc_fresh_screen_audit_2026-10-01.json)

# Corpus screen repair: development result

The schema-visible repair completed29 records, with28 accepted by quote/design consistency checks and one unresolved. The artifact audit checks frozen code/input hashes, exact source excerpts, raw responses, call caps, model digest and record coverage. All articles remain unreviewed for training admission.

## What changed and what happened

| Stage | Input/development set | Agreement with20 single-agent labels |
|---|---|---|
| Baseline | Title/abstract;64 screened articles | TP6, FP4, TN9, FN1 |
| Evidence repair | Additional first-three-paragraph evidence;29 cases | TP0, FP0, TN9, FN0, unresolved11 |
| Schema-visible repair | Same29 cases; enum/schema definitions explicitly in prompt, exact short quotes | TP6, FP0, TN13, FN0, unresolved1 |

The intermediate version suppressed every positive in the reviewed subset, so it was not an improvement. A two-call probe on PMC10464339 isolated schema visibility and design-definition problems; the final regression incorporated those definitions. There is no attribution of benefit to one change alone.

PMC8774900 remains unresolved. Both attempts correctly described directly sampled tissue from three Marfan patients and four controls, but changed the source's lowercase “we” to uppercase “We” in a supposed exact topic quote. The quote gate rejected both attempts. It has not been silently admitted or treated as a negative clinical-study label.

This is an error-informed development regression against one agent's labels, not independent accuracy, expert adjudication or a production corpus filter. The29 cases include nine previously observed failures. Before expanding model-assisted triage, freeze a fresh sample and inspect proposed inclusions against full methods/results. Preserve uncertain cases and distinguish article design from cardiovascular topic.

Evidence: [summary](implementation/pmc_schema_screen_summary_2026-09-30.json), [audit](implementation/pmc_schema_screen_audit_2026-09-30.json), [audit implementation](implementation/audit_pmc_current_checks.py), [protocol](CORPUS_SCREEN_REPAIR_PROTOCOL_2026-09-30.md). Raw prompts/responses are retained in ignored local data.

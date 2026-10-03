# Subject-adversarial development result — 3 October 2026

Job 22007333 completed all 18 cells, exit 0:0, in 391 allocated GPU seconds. No retry or new source fitting. All source/split/timing/array/checkpoint hashes, training-subject mappings/class supports, selected-epoch rules and per-group confusion arithmetic were checked. Six zero-weight controls exactly match previous combined-model MIT/INCART confusion counts and selected epochs, with validation CE differences below 1e-6. Gradient preflight verified sign/scale and unchanged initial rhythm logits.

## Validation selection

Mean subject-disjoint validation CE selects weight 0.05: 0.333936 versus control 0.336657 and weight 0.2 at 0.343947. This choice uses only validation CE, not MIT test or INCART. Report every arm; the externally stronger 0.2 macro score does not change the frozen selection rule.

| Mean over six matched cells | MIT control | MIT selected 0.05 | INCART control | INCART selected 0.05 |
|---|---:|---:|---:|---:|
| Four-class macro F1 | 0.5843 | 0.6005 | 0.4984 | 0.5168 |
| S F1 | 0.4836 | 0.5122 | 0.2741 | 0.3166 |
| S precision | 0.4416 | 0.4935 | 0.1839 | 0.2165 |
| S recall | 0.7071 | 0.6676 | 0.6699 | 0.6763 |
| F recall | 0.0018 | 0.0202 | 0.0495 | 0.0616 |
| F precision | 0.1167 | 0.1806 | 0.0036 | 0.0050 |
| S false positives | 597.8 | 451.7 | 9,132.3 | 5,753.8 |
| F false positives | 5.8 | 9.7 | 2,757.0 | 2,687.0 |
| Multiclass Brier | 0.1054 | 0.1027 | 0.1757 | 0.1515 |

## Frozen decision

Retain the existing combined CNN/timing reference. The selected 0.05 candidate improves mean macro/S-F1, F recall/precision and Brier on both development sources, and reduces INCART S/F false positives. It nevertheless fails the frozen MIT F false-positive guard: 9.67 versus 5.83 mean false positives, above the allowed 110% of control. That ratio is sensitive to the small absolute baseline; disclose the increase of 3.83 mean false positives without changing the prespecified rule after seeing results.

F remains poorly detected: about 2.02% MIT recall and 6.16% INCART recall; INCART F precision is about 0.50%. MIT S recall also drops while precision improves. Thus no rare-class or clinical success claim follows from aggregate improvements. Weight 0.2 has stronger INCART macro/S-F1 but worse validation CE, MIT S-F1/Brier and INCART F precision/false positives; it is not selected.

The adversarial candidate is promising development evidence to preserve, not an accepted reference or independent confirmation. Next work should investigate rare-F morphology/decision errors and validation-only class decision calibration, or synchronized lead representation learning, under a separate frozen protocol. Do not relax this completed ledger’s guard or score SVDB to choose a method. The two partitions and six cells are not six independent cohorts.

Patient identity predictions are training-only. All learned transformations/head fitting use MIT training groups; 201/202 remain together. INCART remains inspected development. EDB is unscored and SVDB sealed. Centered waveform latency and annotation-assisted R peaks still preclude a prospective-monitor claim.

Evidence: implementation/ecg_subject_adversary_audit_2026-10-03.json; ecg_subject_zero_control_audit_2026-10-03.json; ecg_subject_adversary_submission_2026-10-03.json; ECG_SUBJECT_ADVERSARY_PROTOCOL_2026-10-03.md.
